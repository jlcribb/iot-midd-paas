import { describe, expect, it } from "vitest";
import type { PoolClient } from "pg";
import type { ControlActor } from "@/lib/dto/control-access.dto";
import type { TransactionRunner } from "@/lib/db/tx";
import { assertGdssAccess, GDSS_EVALUATE_CAPABILITY } from "@/lib/gdss/service";
import { GdssEvaluationService } from "@/lib/services/gdss-evaluation.service";
import { context, expressionFixture } from "../fixtures/gdss-expression";

const project="00000000-0000-4000-8000-000000000001", version="00000000-0000-4000-8000-000000000010";
const actor=(role:"viewer"|"operator"|"admin", overrides:Partial<ControlActor>={}):ControlActor=>({user_id:"user",display_name:null,auth_source:"oauth_session",role,all_projects:false,project_ids:[project],project_roles:{[project]:role},...overrides});

describe("GDSS-002 EVALUATE_MODEL authorization and adapter isolation", () => {
  it("allows scoped OAuth operator/admin and denies viewer/fallback/missing membership", () => {
    expect(GDSS_EVALUATE_CAPABILITY).toBe("EVALUATE_MODEL");
    expect(()=>assertGdssAccess(actor("operator"),project,"evaluate")).not.toThrow();
    expect(()=>assertGdssAccess(actor("admin"),project,"evaluate")).not.toThrow();
    expect(()=>assertGdssAccess(actor("viewer"),project,"evaluate")).toThrow();
    expect(()=>assertGdssAccess(actor("admin",{auth_source:"dev_fallback"}),project,"evaluate")).toThrow();
    expect(()=>assertGdssAccess(actor("admin",{all_projects:false,project_ids:[],project_roles:{}}),project,"evaluate")).toThrow();
  });
  it("uses project role rather than conflicting global role", () => {
    expect(()=>assertGdssAccess(actor("admin",{project_roles:{[project]:"viewer"}}),project,"evaluate")).toThrow();
    expect(()=>assertGdssAccess(actor("viewer",{project_roles:{[project]:"operator"}}),project,"evaluate")).not.toThrow();
  });
  it("adapter performs one exact-version SELECT and gives no client to pure evaluator", async () => {
    const queries:string[]=[];
    const client={query:async(text:string)=>{queries.push(text);return {rows:[{id:version,project_id:project,content:expressionFixture("hydroponic"),content_hash:"a".repeat(64),lifecycle_status:"DRAFT"}],rowCount:1};}} as unknown as PoolClient;
    const runner:TransactionRunner=async fn=>fn(client);
    const service=new GdssEvaluationService(runner), request=context(version,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}});
    const {projectId:_projectId,modelVersionId:_modelVersionId,...input}=request;
    expect((await service.evaluate(actor("operator"),project,version,input)).status).toBe("SUCCEEDED");
    expect(queries).toHaveLength(1); expect(queries[0].trim().startsWith("SELECT")).toBe(true);
  });
});
