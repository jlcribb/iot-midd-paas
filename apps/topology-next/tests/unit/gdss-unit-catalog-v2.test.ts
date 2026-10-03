import { describe,expect,it } from "vitest";
import type { ModelContent, Provenance, UnitDefinition } from "@/lib/gdss/core";
import { catalogUnit, evaluateExpression, getUnitCatalog, multiplyDimensions, UNIT_CONVERSION_CATALOG_VERSION_V1, UNIT_CONVERSION_CATALOG_VERSION_V2, UNIT_CONVERSION_CATALOG_V1, UNIT_CONVERSION_CATALOG_V2 } from "@/lib/gdss/expression";
import { context, expressionFixture } from "../fixtures/gdss-expression";

const id="00000000-0000-4000-8000-000000000020";
const provenance:Provenance[]=[{kind:"HUMAN_PROPOSED",description:"temporal extension fixture",asserted_by:"test",metadata:{}}];
const second:UnitDefinition={key:"second",revision:1,symbol:"s",name:"second",dimension:[0,0,1,0,0,0,0],scale:1,offset:0,canonical_unit:"second"};
const temporalModel:ModelContent={description:"Temporal unit contract",validity_domain:{},provenance,units:[second],children:[
  {kind:"Variable",symbol:"elapsed",label:"elapsed",description:"",provenance,unit_ref:"second",dimension:second.dimension,computational_role:"INPUT",epistemic_kind:"DERIVED"},
  {kind:"Variable",symbol:"result",label:"result",description:"",provenance,unit_ref:"second",dimension:second.dimension,computational_role:"OUTPUT",epistemic_kind:"DERIVED"},
  {kind:"Formula",symbol:"identity",label:"identity",description:"",provenance,expression_source:"elapsed",input_refs:["elapsed"],output_ref:"result",validity_domain:{}}
]};

describe("GDS2 temporal unit catalog extension",()=>{
  it("defines immutable V1 and explicit immutable V2 successor",()=>{
    expect(Object.isFrozen(UNIT_CONVERSION_CATALOG_V1)).toBe(true);
    expect(Object.isFrozen(UNIT_CONVERSION_CATALOG_V2)).toBe(true);
    expect(Object.keys(UNIT_CONVERSION_CATALOG_V1).sort()).toEqual(Object.keys(UNIT_CONVERSION_CATALOG_V2).filter(key=>key!=="second@1").sort());
    for(const key of Object.keys(UNIT_CONVERSION_CATALOG_V1)) expect(UNIT_CONVERSION_CATALOG_V2[key]).toEqual(UNIT_CONVERSION_CATALOG_V1[key]);
    expect(()=>Object.assign(getUnitCatalog(UNIT_CONVERSION_CATALOG_VERSION_V2),{bad:{}})).toThrow();
  });
  it("defines second@1 only in V2 as the canonical temporal interval",()=>{
    expect(()=>catalogUnit({key:"second",revision:1},undefined,UNIT_CONVERSION_CATALOG_VERSION_V1)).toThrow();
    expect(catalogUnit({key:"second",revision:1},undefined,UNIT_CONVERSION_CATALOG_VERSION_V2)).toEqual(expect.objectContaining({...second,quantitySemantics:["INTERVAL"],affineFamily:false}));
  });
  it("keeps compound units dimensionally coherent with second",()=>{
    const secondDimension=catalogUnit({key:"second",revision:1},undefined,UNIT_CONVERSION_CATALOG_VERSION_V2).dimension;
    expect(multiplyDimensions(catalogUnit({key:"meter_per_second",revision:1},undefined,UNIT_CONVERSION_CATALOG_VERSION_V2).dimension,secondDimension)).toEqual([1,0,0,0,0,0,0]);
    expect(multiplyDimensions(catalogUnit({key:"cubic_meter_per_second",revision:1},undefined,UNIT_CONVERSION_CATALOG_VERSION_V2).dimension,secondDimension)).toEqual([3,0,0,0,0,0,0]);
  });
  it("preserves V1 evaluation and makes catalog choice part of deterministic identity",()=>{
    const model=expressionFixture("hydroponic"), inputs={cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}};
    const v1=evaluateExpression({id,content:model},context(id,"flow_formula",inputs));
    const v1Explicit=evaluateExpression({id,content:model},{...context(id,"flow_formula",inputs),conversionCatalogVersion:UNIT_CONVERSION_CATALOG_VERSION_V1});
    const v2=evaluateExpression({id,content:model},{...context(id,"flow_formula",inputs),conversionCatalogVersion:UNIT_CONVERSION_CATALOG_VERSION_V2});
    expect(v1Explicit).toEqual(v1); expect(v1.status).toBe("SUCCEEDED"); expect(v2.status).toBe("SUCCEEDED");
    if(v1.status==="SUCCEEDED"&&v2.status==="SUCCEEDED") { expect(v2.result).toEqual(v1.result); expect(v2.evaluation_input_hash).not.toBe(v1.evaluation_input_hash); }
  });
  it("accepts second only under V2 and fails unknown or mismatched selection closed",()=>{
    const request=context(id,"identity",{elapsed:{value:2,unit:{key:"second",revision:1}}});
    expect(evaluateExpression({id,content:temporalModel},request).status).toBe("FAILED");
    const v2=evaluateExpression({id,content:temporalModel},{...request,conversionCatalogVersion:UNIT_CONVERSION_CATALOG_VERSION_V2});
    expect(v2.status).toBe("SUCCEEDED"); if(v2.status==="SUCCEEDED") { expect(v2.result.value).toBe(2); expect([...v2.result.dimension]).toEqual(second.dimension); }
    const unknown=evaluateExpression({id,content:temporalModel},{...request,conversionCatalogVersion:"UNKNOWN" as typeof request.conversionCatalogVersion});
    expect(unknown.status).toBe("FAILED"); if(unknown.status==="FAILED") expect(unknown.diagnostics[0].code).toBe("VERSION_MISMATCH");
  });
});
