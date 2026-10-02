import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import ts from "typescript";
import { fixture } from "../fixtures/gdss";
import { canonicalContent, contentHash, validateContent, compatible, lifecycle, nextStatus, modelSchema } from "@/lib/gdss/core";
import { assertGdssAccess, GdssService } from "@/lib/gdss/service";
import type { ControlActor } from "@/lib/dto/control-access.dto";
const project = "00000000-0000-4000-8000-000000000001";
const actor: ControlActor = { user_id: "a", display_name: null, role: "admin", auth_source: "oauth_session", all_projects: false, project_ids: [project], project_roles: { [project]: "operator" } };
describe("GDSS pure contracts and governance", () => {
  it.each(["hydroponic","thermal"] as const)("accepts all six child contracts: %s", d => {
    const m = validateContent(fixture(d)); expect(m.children).toHaveLength(6);
    expect(contentHash(m)).toMatch(/^[a-f0-9]{64}$/);
  });
  it("preserves independent computational/epistemic categories", () => {
    for (const kind of ["OBSERVED","SIMULATED","PREDICTED","DERIVED","CALIBRATED","COUNTERFACTUAL"]) {
      const m = fixture("thermal"); Object.assign(m.children[1], { epistemic_kind: kind, computational_role: "STATE" });
      expect(validateContent(m).children[1]).toMatchObject({ epistemic_kind: kind, computational_role: "STATE" });
    }
    const m = fixture("thermal"); Object.assign(m.children[1], { epistemic_kind: "MEASURED" });
    expect(() => validateContent(m)).toThrow();
  });
  it("rejects foreign references, missing provenance, invalid dimensions and ranges", () => {
    const m = fixture("thermal"); Object.assign(m.children[3], { input_refs: ["other_version"] });
    expect(() => validateContent(m)).toThrow();
    expect(() => validateContent({ ...fixture("thermal"), provenance: [] })).toThrow();
    const n = fixture("thermal"); Object.assign(n.children[1], { dimension: [1,0,0,0,0,0,0] }); expect(() => validateContent(n)).toThrow();
    const p = fixture("thermal"); Object.assign(p.children[2], { default_value: 999 }); expect(() => validateContent(p)).toThrow();
  });
  it("compares SI signatures, including affine units and dimensionless", () => {
    const length = [0,1,0,0,0,0,0] as const;
    expect(compatible([...length],[...length])).toBe(true);
    expect(compatible([0,0,0,0,1,0,0],[0,0,0,0,1,0,0])).toBe(true);
    expect(compatible([...length],[0,0,1,0,0,0,0])).toBe(false);
    expect(compatible([1,-1,-2,0,0,0,0],[1,0,0,0,0,0,0])).toBe(false);
    expect(compatible([0,0,0,0,0,0,0],[0,0,0,0,0,0,0])).toBe(true);
  });
  it("hashes unordered dependencies and preserves ordered semantic arrays", () => {
    const a = fixture("thermal"), b = structuredClone(a);
    b.children.reverse();
    const f = b.children.find(c => c.kind === "Formula")!; if (f.kind === "Formula") f.input_refs.reverse();
    expect(contentHash(a)).toBe(contentHash(b));
    b.validity_domain = { assumptions: ["not calibrated","illustrative"] };
    expect(contentHash(a)).not.toBe(contentHash(b));
    b.description = "changed"; expect(contentHash(a)).not.toBe(contentHash(b));
    expect(canonicalContent(a)).not.toContain("model_version_id");
  });
  it("requires source identity and preserves heterogeneous provenance", () => {
    const m = fixture("thermal");
    m.provenance.push({ kind: "LITERATURE", source_reference: "doi:example", description: "Source", asserted_by: "human", metadata: {} });
    m.provenance.push({ kind: "EMPIRICAL", description: "Observations", asserted_by: "human", metadata: {} });
    expect(JSON.parse(canonicalContent(m)).provenance.map((p: {kind:string}) => p.kind).sort()).toEqual(["AI_PROPOSED","EMPIRICAL","LITERATURE"]);
    delete m.provenance[1].source_reference; expect(() => validateContent(m)).toThrow();
  });
  it("keeps expressions opaque", () => {
    const m = fixture("thermal");
    Object.assign(m.children[3], { expression_source: "globalThis.GDSS_EXECUTED = true" });
    validateContent(m); contentHash(m);
    expect((globalThis as Record<string,unknown>).GDSS_EXECUTED).toBeUndefined();
  });
  it("does not promote calibrated provenance or confer scientific validity", () => {
    const m = fixture("thermal");
    m.provenance[0].kind="CALIBRATED";
    expect(validateContent(m).provenance[0].kind).toBe("CALIBRATED");
    expect(modelSchema.safeParse({...m,scientifically_validated:true}).success).toBe(false);
    expect(modelSchema.safeParse({...m,universally_valid:true}).success).toBe(false);
  });
  it("admits only the linear lifecycle", () => {
    lifecycle.slice(0,-1).forEach((s,i) => expect(nextStatus(s)).toBe(lifecycle[i+1]));
    expect(nextStatus("DEPRECATED")).toBeUndefined();
  });
  it("uses project roles, denies fallback, and separates create/publication authority", () => {
    expect(() => assertGdssAccess(actor,project,"create")).not.toThrow();
    expect(() => assertGdssAccess(actor,project,"publish")).toThrow();
    expect(() => assertGdssAccess({...actor, project_roles: {[project]:"admin"}},project,"publish")).not.toThrow();
    expect(() => assertGdssAccess({...actor, project_roles: {}},project,"edit")).toThrow();
    expect(() => assertGdssAccess({...actor, auth_source:"dev_fallback"},project,"create")).toThrow();
    expect(() => assertGdssAccess(actor,"00000000-0000-4000-8000-000000000002","read")).toThrow();
  });
  it("has a closed declarative surface, rejecting operational payloads", () => {
    const methods = Object.getOwnPropertyNames(GdssService.prototype).filter(n => !["constructor","identity","version","audit"].includes(n)).sort();
    expect(methods).toEqual(["createDraftVersion","createModelIdentity","createSuccessor","getModel","getVersion","listVersions","transition","updateDraft"].sort());
    for (const forbidden of ["run_model","simulate","predict","recommend","publish_mqtt","execute_command","authorize_actuation","bind_telemetry","bind_device"]) {
      expect(modelSchema.safeParse({...fixture("thermal"), [forbidden]:true}).success).toBe(false);
    }
  });
  it("enforces core dependency, execution and domain-vocabulary boundaries through AST", () => {
    const code = readFileSync(resolve("src/lib/gdss/core.ts"),"utf8");
    const ast = ts.createSourceFile("core.ts",code,ts.ScriptTarget.Latest,true);
    const imports: string[] = [];
    const forbidden = new Set(["hydroponic","nutrient","lettuce","plant","greenhouse","room","hvac","heater"]);
    function visit(node: ts.Node) {
      if (ts.isImportDeclaration(node)) imports.push((node.moduleSpecifier as ts.StringLiteral).text);
      if (ts.isIdentifier(node) || ts.isStringLiteral(node))
        for(const token of node.text.toLowerCase().split(/[^a-z]+/)) expect(forbidden.has(token)).toBe(false);
      if (ts.isCallExpression(node)) {
        expect(["eval","exec","require"].includes(node.expression.getText())).toBe(false);
        expect(node.expression.kind).not.toBe(ts.SyntaxKind.ImportKeyword);
      }
      ts.forEachChild(node,visit);
    }
    visit(ast); expect(imports.sort()).toEqual(["node:crypto","zod"]);
    const allowed=new Set(["node:crypto","zod","pg","@/lib/db/tx","@/lib/dto/control-access.dto","@/lib/auth/control-access","@/lib/errors/domain-errors","./core"]);
    for(const name of readdirSync(resolve("src/lib/gdss")).filter(n=>n.endsWith(".ts"))) {
      const source=readFileSync(resolve("src/lib/gdss",name),"utf8");
      const parsed=ts.createSourceFile(name,source,ts.ScriptTarget.Latest,true);
      for(const statement of parsed.statements) if(ts.isImportDeclaration(statement))
        expect(allowed.has((statement.moduleSpecifier as ts.StringLiteral).text)).toBe(true);
      visit(parsed);
    }
  });
});
