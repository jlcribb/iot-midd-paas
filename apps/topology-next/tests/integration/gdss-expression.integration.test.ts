import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { PoolClient } from "pg";
import { pool } from "@/lib/db/pool";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { TransactionRunner } from "@/lib/db/tx";
import { GdssService } from "@/lib/gdss/service";
import { GdssEvaluationService } from "@/lib/services/gdss-evaluation.service";
import { EVALUATOR_VERSION, EXPRESSION_LANGUAGE_VERSION, RESOURCE_LIMITS_PROFILE, UNIT_CONVERSION_CATALOG_VERSION } from "@/lib/gdss/expression";
import { expressionFixture } from "../fixtures/gdss-expression";
import { randomUUID } from "node:crypto";

describe.runIf(process.env.GDSS_DB_TEST === "1")("GDSS-002 read-only lifecycle integration", () => {
  let client:PoolClient, project:string, actor:ControlActor, gdss:GdssService, evaluation:GdssEvaluationService;
  const runner:TransactionRunner=async fn=>fn(client);
  beforeEach(async()=>{
    client=await pool.connect(); await client.query("BEGIN"); project=randomUUID();
    await client.query("INSERT INTO public.projects(id,name) VALUES($1,'gdss-002-rollback-test')",[project]);
    actor={user_id:"gdss-002-test",display_name:null,auth_source:"oauth_session",role:"admin",all_projects:false,project_ids:[project],project_roles:{[project]:"admin"}};
    gdss=new GdssService(runner); evaluation=new GdssEvaluationService(runner);
  });
  afterEach(async()=>{await client.query("ROLLBACK");client.release();});
  it("evaluates every lifecycle state without mutating content, hash, events or audit",async()=>{
    const identity=await gdss.createModelIdentity(actor,project,{canonical_name:randomUUID(),description:"GDSS-002 integration"});
    let version=await gdss.createDraftVersion(actor,project,identity.id,expressionFixture("hydroponic"));
    const input={formulaSymbol:"flow_formula",expressionLanguageVersion:EXPRESSION_LANGUAGE_VERSION,evaluatorVersion:EVALUATOR_VERSION,conversionCatalogVersion:UNIT_CONVERSION_CATALOG_VERSION,resourceLimitsProfile:RESOURCE_LIMITS_PROFILE,inputs:{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}}};
    for(const state of ["DRAFT","VALIDATED","EXPERIMENTAL","APPROVED","PUBLISHED","DEPRECATED"] as const){
      if(state!=="DRAFT") version=await gdss.transition(actor,project,version.id,state,"GDSS-002 lifecycle isolation");
      const before=await client.query("SELECT content,content_hash,lifecycle_status,(SELECT count(*)::int FROM public.gdss_lifecycle_event WHERE model_version_id=v.id) events,(SELECT count(*)::int FROM iot_schema.auditoria WHERE entidad_id=v.id) audits FROM public.gdss_version v WHERE id=$1",[version.id]);
      const result=await evaluation.evaluate(actor,project,version.id,input);
      const after=await client.query("SELECT content,content_hash,lifecycle_status,(SELECT count(*)::int FROM public.gdss_lifecycle_event WHERE model_version_id=v.id) events,(SELECT count(*)::int FROM iot_schema.auditoria WHERE entidad_id=v.id) audits FROM public.gdss_version v WHERE id=$1",[version.id]);
      expect(result).toMatchObject({status:"SUCCEEDED",epistemic_kind:"DERIVED",physical_authority:"NONE"});
      expect(after.rows[0]).toEqual(before.rows[0]);
    }
    expect((await client.query("SELECT to_regclass('public.gdss_expression_evaluation') AS evaluation_table,to_regclass('public.gdss_expression_ast') AS ast_table")).rows[0]).toEqual({evaluation_table:null,ast_table:null});
  });
});
