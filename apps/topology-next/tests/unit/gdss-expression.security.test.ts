import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";
import ts from "typescript";
import { buildDependencyGraph, DEFAULT_EXPRESSION_LIMITS, evaluateAst, evaluateExpression, parseExpression, tokenize } from "@/lib/gdss/expression";
import { context, expressionFixture } from "../fixtures/gdss-expression";

describe("GDSS-002 security and resource boundaries", () => {
  it("contains no forbidden capability imports in the pure expression core", () => {
    const root=resolve("src/lib/gdss/expression"), forbidden=["db","http","mqtt","simulation","promotion","actuation","control-engine","dte","fs","child_process","process"];
    for(const file of readdirSync(root).filter(name=>name.endsWith(".ts"))) {
      const source=readFileSync(resolve(root,file),"utf8"), ast=ts.createSourceFile(file,source,ts.ScriptTarget.Latest,true);
      for(const statement of ast.statements) if(ts.isImportDeclaration(statement)) {
        const module=(statement.moduleSpecifier as ts.StringLiteral).text.toLowerCase();
        expect(forbidden.some(token=>module.includes(token))).toBe(false);
      }
    }
  });
  it("rejects traversal, dynamic invocation and unsupported Unicode", () => {
    for(const source of ["constructor(1)","__proto__.x","prototype[x]","f()(1)","obj.method()","temperatura_ñ+1"])
      expect(() => parseExpression(source)).toThrow();
    expect(() => parseExpression("a".repeat(121))).toThrow();
    expect(() => parseExpression("(".repeat(100)+"1"+")".repeat(100),{...DEFAULT_EXPRESSION_LIMITS,astDepth:16})).toThrow(/resource limit/);
  });
  it("enforces source, token, depth, node, function and operation budgets", () => {
    expect(() => tokenize("1+1",{...DEFAULT_EXPRESSION_LIMITS,sourceLength:3})).not.toThrow();
    expect(() => tokenize("1+1",{...DEFAULT_EXPRESSION_LIMITS,sourceLength:2})).toThrow();
    expect(() => tokenize("1+1",{...DEFAULT_EXPRESSION_LIMITS,tokenCount:4})).not.toThrow();
    expect(() => tokenize("1+1",{...DEFAULT_EXPRESSION_LIMITS,tokenCount:3})).toThrow();
    expect(() => parseExpression("1",{...DEFAULT_EXPRESSION_LIMITS,astDepth:5})).not.toThrow();
    expect(() => parseExpression("1",{...DEFAULT_EXPRESSION_LIMITS,astDepth:4})).toThrow();
    expect(() => parseExpression("1+2",{...DEFAULT_EXPRESSION_LIMITS,astNodes:3})).not.toThrow();
    expect(() => parseExpression("1+2",{...DEFAULT_EXPRESSION_LIMITS,astNodes:2})).toThrow();
    expect(() => parseExpression("abs(abs(1))",{...DEFAULT_EXPRESSION_LIMITS,functionNesting:2})).not.toThrow();
    expect(() => parseExpression("abs(abs(1))",{...DEFAULT_EXPRESSION_LIMITS,functionNesting:1})).toThrow();
    const parsed=parseExpression("1+2");
    expect(() => evaluateAst(parsed.ast,new Map(),{...DEFAULT_EXPRESSION_LIMITS,evaluatorOperations:3})).not.toThrow();
    expect(() => evaluateAst(parsed.ast,new Map(),{...DEFAULT_EXPRESSION_LIMITS,evaluatorOperations:2})).toThrow();
  });
  it("enforces symbol, graph and supplied-input budgets", () => {
    const model=expressionFixture("hydroponic"), id="00000000-0000-4000-8000-000000000010";
    const request=context(id,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}});
    expect(evaluateExpression({id,content:model},request,{...DEFAULT_EXPRESSION_LIMITS,distinctSymbols:2,dependencyNodes:3,dependencyEdges:2,suppliedInputs:2}).status).toBe("SUCCEEDED");
    for(const limits of [{...DEFAULT_EXPRESSION_LIMITS,distinctSymbols:1},{...DEFAULT_EXPRESSION_LIMITS,dependencyNodes:2},{...DEFAULT_EXPRESSION_LIMITS,dependencyEdges:1},{...DEFAULT_EXPRESSION_LIMITS,suppliedInputs:1}])
      expect(evaluateExpression({id,content:model},request,limits).status).toBe("FAILED");
    expect(() => buildDependencyGraph([{formula:"f",output:"a",inputs:["b","c"]}],{...DEFAULT_EXPRESSION_LIMITS,dependencyNodes:3,dependencyEdges:2})).not.toThrow();
  });
  it("keeps result contract closed to physical and governance authority", () => {
    const model=expressionFixture("hydroponic"), id="00000000-0000-4000-8000-000000000010";
    const result=evaluateExpression({id,content:model},context(id,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}}));
    expect(result).toMatchObject({status:"SUCCEEDED",physical_authority:"NONE",epistemic_kind:"DERIVED"});
    for(const forbidden of ["controlPolicy","deploymentAuthorization","deploymentIntent","actuationAuthorization","actuationIntent","actuationCommand","simulationRun"])
      expect(forbidden in result).toBe(false);
  });
  it("bounded benchmark completes repeated neutral evaluations", () => {
    const model=expressionFixture("hydroponic"), id="00000000-0000-4000-8000-000000000010", request=context(id,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}});
    const start=performance.now(); for(let i=0;i<500;i++) expect(evaluateExpression({id,content:model},request).status).toBe("SUCCEEDED");
    const durationMs=performance.now()-start;
    const budgetMs=5000;
    if(process.env.GDSS_BENCHMARK_REPORT==="1") console.info(JSON.stringify({benchmark:"GDSS_EXPR_V1",evaluations:500,duration_ms:Number(durationMs.toFixed(3)),budget_ms:budgetMs,status:durationMs<budgetMs?"PASS":"FAIL"}));
    expect(durationMs).toBeLessThan(budgetMs);
  });
});
