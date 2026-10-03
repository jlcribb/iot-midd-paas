import { describe, expect, it } from "vitest";
import { evaluateExpression, type EvaluationInputs } from "@/lib/gdss/expression";
import { affineFixture, context, expressionFixture } from "../fixtures/gdss-expression";

const id="00000000-0000-4000-8000-000000000010";
const snapshot=(content:ReturnType<typeof expressionFixture>|ReturnType<typeof affineFixture>)=>({id,content,content_hash:"a".repeat(64),lifecycle_status:"PUBLISHED"});

describe("GDSS-002 pure deterministic evaluation", () => {
  it.each(["hydroponic","thermal"] as const)("evaluates neutral %s fixture through the same pipeline", domain => {
    const model=expressionFixture(domain);
    const inputs: EvaluationInputs=domain==="hydroponic"?{
      cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}
    }:{
      thermal_transmittance:{value:2,unit:{key:"watt_per_square_meter_kelvin",revision:1}},area:{value:5,unit:{key:"square_meter",revision:1}},temperature_difference:{value:10,unit:{key:"kelvin",revision:1},quantitySemantics:"INTERVAL" as const}
    };
    const result=evaluateExpression(snapshot(model),context(id,domain==="hydroponic"?"flow_formula":"heat_formula",inputs));
    expect(result.status).toBe("SUCCEEDED");
    if(result.status==="SUCCEEDED") expect(result.result.value).toBe(domain==="hydroponic"?6:100);
  });
  it("converts 20 Celsius absolute to 293.15 Kelvin absolute", () => {
    const result=evaluateExpression(snapshot(affineFixture("convert")),context(id,"affine_formula",{temperature:{value:20,unit:{key:"celsius",revision:1},quantitySemantics:"ABSOLUTE"}},{requestedOutputUnit:{key:"kelvin",revision:1},expectedOutputQuantitySemantics:"ABSOLUTE"}));
    expect(result.status).toBe("SUCCEEDED"); if(result.status==="SUCCEEDED") expect(result.result).toMatchObject({value:293.15,quantitySemantics:"ABSOLUTE"});
  });
  it("converts a Celsius interval without offset", () => {
    const result=evaluateExpression(snapshot(affineFixture("convert")),context(id,"affine_formula",{temperature:{value:10,unit:{key:"celsius",revision:1},quantitySemantics:"INTERVAL"}},{requestedOutputUnit:{key:"kelvin",revision:1},expectedOutputQuantitySemantics:"INTERVAL"}));
    expect(result.status).toBe("SUCCEEDED"); if(result.status==="SUCCEEDED") expect(result.result.value).toBe(10);
  });
  it("derives absolute subtraction as interval", () => {
    const result=evaluateExpression(snapshot(affineFixture("subtract")),context(id,"affine_formula",{hot:{value:20,unit:{key:"celsius",revision:1},quantitySemantics:"ABSOLUTE"},cold:{value:10,unit:{key:"celsius",revision:1},quantitySemantics:"ABSOLUTE"}},{expectedOutputQuantitySemantics:"INTERVAL"}));
    expect(result.status).toBe("SUCCEEDED"); if(result.status==="SUCCEEDED") expect(result.result).toMatchObject({value:10,quantitySemantics:"INTERVAL"});
  });
  it("adds interval to absolute and rejects absolute plus absolute", () => {
    const model=snapshot(affineFixture("add"));
    const good=evaluateExpression(model,context(id,"affine_formula",{base:{value:20,unit:{key:"celsius",revision:1},quantitySemantics:"ABSOLUTE"},change:{value:10,unit:{key:"celsius",revision:1},quantitySemantics:"INTERVAL"}},{expectedOutputQuantitySemantics:"ABSOLUTE"}));
    expect(good.status).toBe("SUCCEEDED"); if(good.status==="SUCCEEDED") expect(good.result.value).toBe(30);
    const bad=evaluateExpression(model,context(id,"affine_formula",{base:{value:20,unit:{key:"celsius",revision:1},quantitySemantics:"ABSOLUTE"},change:{value:10,unit:{key:"celsius",revision:1},quantitySemantics:"ABSOLUTE"}},{expectedOutputQuantitySemantics:"ABSOLUTE"}));
    expect(bad.status).toBe("FAILED"); if(bad.status==="FAILED") expect(bad.diagnostics[0].code).toBe("AFFINE_QUANTITY_ERROR");
  });
  it("fails missing/extra/non-finite inputs and unsupported unit definitions", () => {
    const model=expressionFixture("hydroponic"), base=context(id,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}}});
    for(const request of [base,{...base,inputs:{...base.inputs,fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}},extra:{value:1,unit:{key:"meter",revision:1}}}},{...base,inputs:{cross_section_area:{value:Infinity,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}}}])
      expect(evaluateExpression(snapshot(model),request).status).toBe("FAILED");
    const corrupt=structuredClone(model); corrupt.units[0].scale=2;
    expect(evaluateExpression(snapshot(corrupt),context(id,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}})).status).toBe("FAILED");
  });
  it("emits exact ownership and symbol diagnostics", () => {
    const model=expressionFixture("hydroponic"), base=context(id,"flow_formula",{});
    const code=(result:ReturnType<typeof evaluateExpression>)=>{expect(result.status).toBe("FAILED");return result.diagnostics[0].code;};
    expect(code(evaluateExpression({id:"00000000-0000-4000-8000-000000000099",content:model},base))).toBe("CROSS_VERSION_REFERENCE");
    const unknown=structuredClone(model), formula=unknown.children.find(child=>child.kind==="Formula")!;
    if(formula.kind==="Formula") formula.input_refs=["missing"];
    expect(code(evaluateExpression(snapshot(unknown),base))).toBe("UNKNOWN_SYMBOL");
    const invalid=structuredClone(model), invalidFormula=invalid.children.find(child=>child.kind==="Formula")!;
    if(invalidFormula.kind==="Formula") invalidFormula.input_refs=["flow_formula"];
    expect(code(evaluateExpression(snapshot(invalid),base))).toBe("INVALID_SYMBOL_KIND");
    const ambiguous=structuredClone(model); ambiguous.children.push(structuredClone(ambiguous.children[0]));
    expect(code(evaluateExpression(snapshot(ambiguous),base))).toBe("AMBIGUOUS_SYMBOL");
    const mismatch=structuredClone(model), mismatchFormula=mismatch.children.find(child=>child.kind==="Formula")!;
    if(mismatchFormula.kind==="Formula") mismatchFormula.input_refs=["cross_section_area"];
    expect(code(evaluateExpression(snapshot(mismatch),base))).toBe("DECLARED_DEPENDENCY_MISMATCH");
  });
  it("keeps hashes deterministic, derived and separate from content identity", () => {
    const model=expressionFixture("hydroponic"), request=context(id,"flow_formula",{cross_section_area:{value:2,unit:{key:"square_meter",revision:1}},fluid_velocity:{value:3,unit:{key:"meter_per_second",revision:1}}});
    const before=snapshot(model), a=evaluateExpression(before,request), b=evaluateExpression(before,request);
    expect(a).toEqual(b); expect(before.content_hash).toBe("a".repeat(64));
    if(a.status==="SUCCEEDED") {
      expect(a).toMatchObject({epistemic_kind:"DERIVED",physical_authority:"NONE"});
      const changed=evaluateExpression(before,{...request,inputs:{...request.inputs,cross_section_area:{value:4,unit:{key:"square_meter",revision:1}}}});
      expect(changed.status).toBe("SUCCEEDED"); if(changed.status==="SUCCEEDED") expect(changed.evaluation_result_hash).not.toBe(a.evaluation_result_hash);
    }
  });
});
