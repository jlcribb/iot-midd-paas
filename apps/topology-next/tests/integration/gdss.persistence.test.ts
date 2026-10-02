import { beforeEach, afterEach, describe, it, expect, vi } from "vitest";
import * as gdssCore from "@/lib/gdss/core";
import { randomUUID } from "node:crypto";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import type { TransactionRunner } from "@/lib/db/tx";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import { GdssService } from "@/lib/gdss/service";
import { canonicalContent, contentHash, lifecycle } from "@/lib/gdss/core";
import { fixture } from "../fixtures/gdss";

describe.runIf(process.env.GDSS_DB_TEST === "1")("GDSS PostgreSQL transactional invariants", () => {
  let client: PoolClient, project: string, actor: ControlActor, service: GdssService;
  let failOn: string | undefined;
  const runner: TransactionRunner = async fn => {
    await client.query("SAVEPOINT gdss_test_operation");
    try {
      const proxy = new Proxy(client, {
        get(target, property) {
          if (property === "query") return (...args: unknown[]) => {
            if (failOn && String(args[0]).includes(failOn)) throw Error("injected database failure");
            return (target.query as (...a: unknown[]) => unknown).apply(target,args);
          };
          return Reflect.get(target,property);
        }
      });
      const value = await fn(proxy);
      await client.query("SET CONSTRAINTS ALL IMMEDIATE");
      await client.query("SET CONSTRAINTS ALL DEFERRED");
      await client.query("RELEASE SAVEPOINT gdss_test_operation");
      return value;
    } catch (e) {
      await client.query("ROLLBACK TO SAVEPOINT gdss_test_operation");
      throw e;
    }
  };
  beforeEach(async () => {
    failOn = undefined; project = randomUUID(); client = await pool.connect();
    await client.query("BEGIN");
    await client.query("INSERT INTO public.projects(id,name) VALUES($1,'gdss-rollback-test')",[project]);
    actor = { user_id: "gdss-test", display_name: null, auth_source: "oauth_session", role: "admin", all_projects: false, project_ids: [project], project_roles: {[project]:"admin"} };
    service = new GdssService(runner);
  });
  afterEach(async () => { vi.restoreAllMocks(); if(client) { await client.query("ROLLBACK"); client.release(); } });
  async function draft(domain: "hydroponic" | "thermal" = "thermal") {
    const identity = await service.createModelIdentity(actor,project,{canonical_name:randomUUID(),description:"fixture"});
    return service.createDraftVersion(actor,project,identity.id,fixture(domain));
  }
  async function rejected(sql: string, params: unknown[] = []) {
    await expect(runner(async tx => { await tx.query(sql,params); })).rejects.toThrow();
  }
  it.each(["hydroponic","thermal"] as const)("persists, freezes, audits and versions %s with the same service", async domain => {
    let v = await draft(domain);
    v = await service.updateDraft(actor,project,v.id,fixture(domain));
    for (const state of lifecycle.slice(1)) {
      v = await service.transition(actor,project,v.id,state as Exclude<typeof state,"DRAFT">,"governance review");
      expect(v.content_hash).toBe(contentHash(fixture(domain)));
      for (const child of v.content.children) {
        const edit = structuredClone(v.content);
        edit.children.find(c => c.symbol === child.symbol)!.description = "changed";
        await expect(service.updateDraft(actor,project,v.id,edit)).rejects.toThrow();
      }
      await rejected("UPDATE public.gdss_version SET content=jsonb_set(content,'{description}','\"changed\"') WHERE id=$1",[v.id]);
      await rejected("UPDATE public.gdss_artifact SET payload='{}' WHERE model_version_id=$1",[v.id]);
      await rejected("DELETE FROM public.gdss_version WHERE id=$1",[v.id]);
    }
    const events = await client.query("SELECT * FROM public.gdss_lifecycle_event WHERE model_version_id=$1",[v.id]);
    expect(events.rows).toHaveLength(5);
    expect(events.rows.every(e => e.actor === actor.user_id)).toBe(true);
    const audit = await client.query("SELECT * FROM iot_schema.auditoria WHERE entidad_id=$1 AND accion='GDSS_LIFECYCLE_TRANSITION'",[v.id]);
    expect(audit.rows).toHaveLength(5);
    const next = await service.createSuccessor(actor,project,v.id);
    expect(next.id).not.toBe(v.id); expect(next.predecessor_version_id).toBe(v.id);
    expect(contentHash(next.content)).toBe(v.content_hash);
    const edited = structuredClone(next.content); edited.description = "new hypothesis";
    await service.updateDraft(actor,project,next.id,edited);
    expect((await service.getVersion(actor,project,v.id)).content_hash).toBe(v.content_hash);
    const children = (await service.getVersion(actor,project,next.id)).children;
    expect(children.every(c => c.model_version_id === next.id)).toBe(true);
    expect((await client.query("SELECT DISTINCT model_version_id FROM public.gdss_reference WHERE model_version_id=ANY($1::uuid[])",[[v.id,next.id]])).rows).toHaveLength(2);
  });
  it("denies skipped lifecycle and publication without project authority", async () => {
    const v = await draft();
    for (const target of ["APPROVED","PUBLISHED"] as const) await expect(service.transition(actor,project,v.id,target,"skip")).rejects.toThrow();
    const operator = {...actor,project_roles:{[project]:"operator" as const}};
    for (const target of ["VALIDATED","EXPERIMENTAL","APPROVED"] as const) await service.transition(actor,project,v.id,target,"review");
    await expect(service.transition(operator,project,v.id,"PUBLISHED","publish")).rejects.toThrow();
    await service.transition(actor,project,v.id,"PUBLISHED","publish");
    await rejected("UPDATE public.gdss_version SET lifecycle_status='DRAFT' WHERE id=$1",[v.id]);
    await service.transition(actor,project,v.id,"DEPRECATED","deprecate");
    await rejected("UPDATE public.gdss_version SET lifecycle_status='PUBLISHED' WHERE id=$1",[v.id]);
  });
  it.each(["gdss_lifecycle_event","iot_schema.auditoria","UPDATE public.gdss_version"])("rolls back controlled failure at %s", async point => {
    const v = await draft(); failOn = point;
    await expect(service.transition(actor,project,v.id,"VALIDATED","review")).rejects.toThrow("injected");
    failOn = undefined;
    const current = await service.getVersion(actor,project,v.id);
    expect(current.lifecycle_status).toBe("DRAFT"); expect(current.content_hash).toBeNull();
    expect((await client.query("SELECT * FROM public.gdss_lifecycle_event WHERE model_version_id=$1",[v.id])).rows).toHaveLength(0);
  });
  it("rejects orphan events, transitions without events and incorrect hashes", async () => {
    const v = await draft();
    await rejected("INSERT INTO public.gdss_lifecycle_event(model_version_id,from_status,to_status,actor,reason) VALUES($1,'DRAFT','VALIDATED','x','x')",[v.id]);
    await rejected("UPDATE public.gdss_version SET lifecycle_status='VALIDATED',canonical_content=$2,content_hash=$3 WHERE id=$1",[v.id,canonicalContent(v.content),contentHash(v.content)]);
    await rejected("UPDATE public.gdss_version SET lifecycle_status='VALIDATED',canonical_content=$2,content_hash=$3 WHERE id=$1",[v.id,canonicalContent(v.content),"0".repeat(64)]);
    expect((await service.getVersion(actor,project,v.id)).lifecycle_status).toBe("DRAFT");
  });
  it("rejects cross-version edges, preserves mixed provenance and catalog history", async () => {
    const v = await draft(), other = await draft("hydroponic");
    const invalid = structuredClone(v.content);
    const f = invalid.children.find(c => c.kind === "Formula")!; if(f.kind === "Formula") f.input_refs=["water_temperature"];
    await expect(service.updateDraft(actor,project,v.id,invalid)).rejects.toThrow();
    await rejected("INSERT INTO public.gdss_reference VALUES($1,'relation','water_temperature')",[v.id]);
    const m = structuredClone(v.content);
    m.provenance.push({kind:"LITERATURE",source_reference:"doi:example",description:"source",asserted_by:"x",metadata:{}});
    m.provenance.push({kind:"EMPIRICAL",description:"source",asserted_by:"x",metadata:{}});
    await service.updateDraft(actor,project,v.id,m);
    for(const state of ["VALIDATED","EXPERIMENTAL","APPROVED","PUBLISHED"] as const) await service.transition(actor,project,v.id,state,"review");
    const kinds = (await client.query("SELECT DISTINCT record->>'kind' AS kind FROM public.gdss_provenance WHERE model_version_id=$1",[v.id])).rows.map(r=>r.kind).sort();
    expect(kinds).toEqual(["AI_PROPOSED","EMPIRICAL","LITERATURE"]);
    await rejected("UPDATE public.gdss_unit_definition SET definition='{}' WHERE key='kelvin'");
    await rejected("DELETE FROM public.gdss_provenance WHERE model_version_id=$1",[v.id]);
    const correction=structuredClone(other.content); correction.units[0].offset=1;
    await expect(service.updateDraft(actor,project,other.id,correction)).rejects.toThrow("immutable");
    correction.units[0].revision=2; await service.updateDraft(actor,project,other.id,correction);
    expect((await service.getVersion(actor,project,v.id)).content.units[0].offset).toBe(0);
  });
  it("independent identities and successors have the same semantic hash", async () => {
    const a = await draft(), b = await draft();
    const av=await service.transition(actor,project,a.id,"VALIDATED","review");
    const bv=await service.transition(actor,project,b.id,"VALIDATED","review");
    expect(av.content_hash).toBe(bv.content_hash);
    const successor=await service.createSuccessor(actor,project,a.id);
    expect(contentHash(successor.content)).toBe(av.content_hash);
  });
  it("rolls back hash failure and invalid draft validation without events", async () => {
    const v = await draft();
    vi.spyOn(gdssCore,"contentHash").mockImplementationOnce(() => { throw Error("hash failure"); });
    await expect(service.transition(actor,project,v.id,"VALIDATED","review")).rejects.toThrow("hash failure");
    expect((await service.getVersion(actor,project,v.id)).lifecycle_status).toBe("DRAFT");
    const invalid = structuredClone(v.content); invalid.provenance = [];
    await expect(service.updateDraft(actor,project,v.id,invalid)).rejects.toThrow();
    expect((await client.query("SELECT * FROM public.gdss_lifecycle_event WHERE model_version_id=$1",[v.id])).rows).toHaveLength(0);
  });
  it("enforces version-local foreign keys during SQL aggregate projection", async () => {
    const v = await draft();
    const invalid = structuredClone(v.content);
    const f = invalid.children.find(c => c.kind==="Formula")!;
    if(f.kind==="Formula") f.input_refs=["missing_quantity"];
    await rejected("UPDATE public.gdss_version SET content=$2::jsonb WHERE id=$1",[v.id,JSON.stringify(invalid)]);
    const constraints = await client.query("SELECT pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conrelid='public.gdss_reference'::regclass AND contype='f'");
    expect(constraints.rows).toHaveLength(2);
    expect(constraints.rows.every(r=>r.definition.includes("model_version_id"))).toBe(true);
    expect((await service.getVersion(actor,project,v.id)).content).toEqual(v.content);
  });
  it("rejects SQL documents missing mandatory provenance or dimension semantics", async () => {
    const v=await draft();
    const missing=structuredClone(v.content) as Record<string,unknown>;
    delete missing.provenance;
    await rejected("UPDATE public.gdss_version SET content=$2::jsonb WHERE id=$1",[v.id,JSON.stringify(missing)]);
    const invalid=structuredClone(v.content);
    Object.assign(invalid.children.find(c=>c.kind==="Variable")!,{dimension:[1,0,0,0,0,0,0]});
    await rejected("UPDATE public.gdss_version SET content=$2::jsonb WHERE id=$1",[v.id,JSON.stringify(invalid)]);
    const literature=structuredClone(v.content);
    literature.provenance[0].kind="LITERATURE";
    await rejected("UPDATE public.gdss_version SET content=$2::jsonb WHERE id=$1",[v.id,JSON.stringify(literature)]);
    expect((await service.getVersion(actor,project,v.id)).content).toEqual(v.content);
  });
});
