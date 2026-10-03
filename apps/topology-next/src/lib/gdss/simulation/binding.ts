import { contentHash, type DimensionDefinition, type ModelContent } from "@/lib/gdss/core";
import { analyzeAst, evaluateAst, type SemanticValue } from "@/lib/gdss/expression/evaluator";
import { dimensionsEqual, divideDimensions } from "@/lib/gdss/expression/dimensions";
import { parseExpression } from "@/lib/gdss/expression/parser";
import { DEFAULT_EXPRESSION_LIMITS } from "@/lib/gdss/expression/limits";
import type { DynamicBindingContent, DynamicBindingSnapshot, FormulaEvaluation, SimulationInputManifest, SimulationProgram } from "./contracts";
import { dynamicBindingHash } from "./canonical";
import { simulationFail } from "./diagnostics";
import { GDSS_SIM_LIMITS_V1 } from "./limits";
import { TIME_DIMENSION, validateTemporalConfiguration } from "./temporal";
import { CONSTRAINT_POLICY, DYNAMIC_SEMANTIC_VERSION, SOLVER_VERSION } from "./versions";
import { UNIT_CONVERSION_CATALOG_VERSION_V2 } from "@/lib/gdss/expression/versions";

type ModelFormula = Extract<ModelContent["children"][number],{kind:"Formula"}>;
const astOperations = (node:ReturnType<typeof parseExpression>["ast"]):number => node.kind === "NumericLiteral" || node.kind === "SymbolReference" ? 1 : node.kind === "UnaryExpression" ? 1+astOperations(node.operand) : node.kind === "BinaryExpression" ? 1+astOperations(node.left)+astOperations(node.right) : 1+node.arguments.reduce((sum,item)=>sum+astOperations(item),0);

function assertCounts(content:DynamicBindingContent) {
  const checks:[number,number,string][] = [
    [content.states.length,GDSS_SIM_LIMITS_V1.states,"states"], [content.rates.length,GDSS_SIM_LIMITS_V1.rates,"rates"],
    [content.algebraics.length,GDSS_SIM_LIMITS_V1.algebraicBindings,"algebraics"], [content.parameters.length,GDSS_SIM_LIMITS_V1.parameterBindings,"parameters"],
    [content.constraintRefs.length,GDSS_SIM_LIMITS_V1.constraints,"constraints"]
  ];
  for (const [actual,limit,name] of checks) if (actual > limit) simulationFail("RESOURCE_LIMIT_EXCEEDED","PREFLIGHT",`${name} exceed GDSS_SIM_LIMITS_V1`,{details:{actual,limit}});
  if (content.states.length === 0 || content.rates.length !== content.states.length) simulationFail("INVALID_BINDING","PREFLIGHT","Every state requires exactly one rate");
}

export function validateDynamicBinding(modelVersion:{id:string;content_hash:string|null;content:ModelContent}, content:DynamicBindingContent) {
  if (content.modelVersionId !== modelVersion.id || !modelVersion.content_hash || content.modelContentHash !== modelVersion.content_hash || contentHash(modelVersion.content) !== modelVersion.content_hash)
    simulationFail("CROSS_VERSION_REFERENCE","PREFLIGHT","Binding does not match the exact governed model version");
  if (content.dynamicSemanticVersion !== DYNAMIC_SEMANTIC_VERSION) simulationFail("VERSION_MISMATCH","PREFLIGHT","Unsupported dynamic semantic version");
  assertCounts(content);
  const children = new Map(modelVersion.content.children.map(child=>[child.symbol,child]));
  const units = new Map(modelVersion.content.units.map(unit=>[unit.key,unit]));
  const stateRefs = new Set<string>(), rateRefs = new Set<string>(), outputRefs = new Set<string>();
  for (const state of content.states) {
    if (state.role !== "STATE" || stateRefs.has(state.stateRef)) simulationFail("INVALID_BINDING","PREFLIGHT","STATE roles must be explicit and unique",{stateRef:state.stateRef});
    const artifact=children.get(state.stateRef), unit=units.get(state.unit.key);
    if (!artifact || artifact.kind!=="Variable" || !unit || unit.revision!==state.unit.revision || !dimensionsEqual(artifact.dimension,state.dimension) || !dimensionsEqual(unit.dimension,state.dimension)) simulationFail("INVALID_BINDING","PREFLIGHT","State binding does not resolve exactly",{stateRef:state.stateRef});
    stateRefs.add(state.stateRef);
  }
  for (const rate of content.rates) {
    if (rate.role!=="RATE" || rateRefs.has(rate.rateRef) || outputRefs.has(rate.outputRef) || !stateRefs.has(rate.stateRef)) simulationFail("INVALID_BINDING","PREFLIGHT","RATE roles must map one-to-one to states",{rateRef:rate.rateRef});
    const formula=children.get(rate.formulaRef), output=children.get(rate.outputRef), unit=units.get(rate.unit.key);
    const state=content.states.find(item=>item.stateRef===rate.stateRef)!;
    const expected=divideDimensions(state.dimension,[...TIME_DIMENSION] as DimensionDefinition);
    if (!formula || formula.kind!=="Formula" || formula.output_ref!==rate.outputRef || !output || output.kind!=="Variable" || !unit || unit.revision!==rate.unit.revision || !dimensionsEqual(rate.dimension,expected) || !dimensionsEqual(output.dimension,rate.dimension) || !dimensionsEqual(unit.dimension,rate.dimension)) simulationFail("DIMENSION_FAILURE","PREFLIGHT","Rate dimension must equal state dimension divided by TIME",{rateRef:rate.rateRef,details:{expected,actual:rate.dimension}});
    rateRefs.add(rate.rateRef); outputRefs.add(rate.outputRef);
  }
  if (content.states.some(state=>content.rates.filter(rate=>rate.stateRef===state.stateRef).length!==1)) simulationFail("INVALID_BINDING","PREFLIGHT","Each state requires exactly one rate");
  const algebraicOutputs=new Set(content.algebraics.map(item=>item.outputRef));
  if (algebraicOutputs.size!==content.algebraics.length) simulationFail("INVALID_BINDING","PREFLIGHT","Algebraic outputs must be unique");
  const graph=new Map<string,string[]>();
  for (const algebraic of content.algebraics) {
    const formula=children.get(algebraic.formulaRef), output=children.get(algebraic.outputRef);
    if (algebraic.role!=="ALGEBRAIC" || !formula || formula.kind!=="Formula" || formula.output_ref!==algebraic.outputRef || !output || output.kind!=="Variable") simulationFail("INVALID_BINDING","PREFLIGHT","Algebraic binding does not resolve exactly");
    graph.set(algebraic.outputRef,formula.input_refs.filter(ref=>algebraicOutputs.has(ref)));
  }
  const visiting=new Set<string>(), visited=new Set<string>(), order:string[]=[];
  const visit=(symbol:string)=>{ if(visiting.has(symbol)) simulationFail("INSTANTANEOUS_ALGEBRAIC_LOOP_UNSUPPORTED","PREFLIGHT","Instantaneous algebraic cycle is unsupported"); if(visited.has(symbol)) return; visiting.add(symbol); for(const dependency of graph.get(symbol)??[]) visit(dependency); visiting.delete(symbol); visited.add(symbol); order.push(symbol); };
  [...graph.keys()].sort().forEach(visit);
  return { content:Object.freeze(structuredClone(content)), hash:dynamicBindingHash(content), algebraicOrder:Object.freeze(order) };
}

function snapshotContent(binding:DynamicBindingSnapshot):DynamicBindingContent {
  return {projectId:binding.projectId,modelVersionId:binding.modelVersionId,modelContentHash:binding.modelContentHash,dynamicSemanticVersion:binding.dynamicSemanticVersion,states:binding.states,rates:binding.rates,algebraics:binding.algebraics,parameters:binding.parameters,constraintRefs:binding.constraintRefs,provenanceIdentities:binding.provenanceIdentities};
}

function quantityMap(model:ModelContent, values:Record<string,number>):Map<string,SemanticValue> {
  const result=new Map<string,SemanticValue>();
  for(const [symbol,value] of Object.entries(values)) {
    const artifact=model.children.find(child=>child.symbol===symbol);
    if(!artifact || (artifact.kind!=="Variable" && artifact.kind!=="Parameter")) simulationFail("INVALID_BINDING","RATE","Formula input is not an exact quantity",{details:{symbol}});
    result.set(symbol,{value,dimension:artifact.dimension});
  }
  return result;
}

export function compileSimulationProgram(binding:DynamicBindingSnapshot, manifest:SimulationInputManifest):SimulationProgram {
  if (binding.lifecycleStatus!=="PUBLISHED") simulationFail("INVALID_BINDING","PREFLIGHT","Only PUBLISHED dynamic bindings are executable");
  const validated=validateDynamicBinding({id:binding.modelVersionId,content_hash:binding.modelContentHash,content:binding.model},snapshotContent(binding));
  if (binding.dynamicBindingHash!==validated.hash) simulationFail("INVALID_BINDING","PREFLIGHT","Dynamic binding hash mismatch");
  if (manifest.modelVersionId!==binding.modelVersionId || manifest.modelContentHash!==binding.modelContentHash || manifest.bindingId!==binding.bindingId || manifest.bindingVersionId!==binding.bindingVersionId || manifest.dynamicBindingHash!==binding.dynamicBindingHash) simulationFail("CROSS_VERSION_REFERENCE","PREFLIGHT","Simulation manifest does not match exact binding/model identity");
  if (manifest.dynamicSemanticVersion!==DYNAMIC_SEMANTIC_VERSION || manifest.solverVersion!==SOLVER_VERSION || manifest.unitConversionCatalogVersion!==UNIT_CONVERSION_CATALOG_VERSION_V2 || manifest.constraintPolicy!==CONSTRAINT_POLICY || manifest.resourceProfile.profileVersion!==GDSS_SIM_LIMITS_V1.profileVersion) simulationFail("VERSION_MISMATCH","PREFLIGHT","Simulation version contract mismatch");
  validateTemporalConfiguration(manifest.temporalConfiguration);
  const formulas=new Map<string,{formula:ModelFormula;ast:ReturnType<typeof parseExpression>["ast"];operations:number}>();
  for(const ref of [...binding.algebraics.map(v=>v.formulaRef),...binding.rates.map(v=>v.formulaRef)]) {
    const child=binding.model.children.find(item=>item.symbol===ref);
    if(!child || child.kind!=="Formula") simulationFail("INVALID_BINDING","PREFLIGHT","Formula reference is not local to exact model version",{formulaRef:ref});
    const ast=parseExpression(child.expression_source,DEFAULT_EXPRESSION_LIMITS).ast;
    formulas.set(ref,{formula:child,ast,operations:astOperations(ast)});
  }
  const evaluate=(formulaRef:string,values:Record<string,number>):FormulaEvaluation=>{
    const compiled=formulas.get(formulaRef)!; const symbols=quantityMap(binding.model,values);
    const dimensional=analyzeAst(compiled.ast,symbols);
    const output=binding.model.children.find(item=>item.symbol===compiled.formula.output_ref);
    if(!output || (output.kind!=="Variable" && output.kind!=="Parameter") || !dimensionsEqual(dimensional.dimension,output.dimension)) simulationFail("DIMENSION_FAILURE","RATE","Expression output dimension mismatch",{formulaRef});
    return {value:evaluateAst(compiled.ast,symbols,DEFAULT_EXPRESSION_LIMITS),operations:compiled.operations};
  };
  return {
    binding,manifest,
    evaluateAlgebraics(snapshot,parameters){ const values={...parameters,...snapshot}, result:Record<string,FormulaEvaluation>={}; for(const outputRef of validated.algebraicOrder){ const item=binding.algebraics.find(a=>a.outputRef===outputRef)!; const evaluated=evaluate(item.formulaRef,{...values,...Object.fromEntries(Object.entries(result).map(([k,v])=>[k,v.value]))}); result[outputRef]=evaluated; } return result; },
    evaluateRates(snapshot,algebraics,parameters){ const values={...parameters,...snapshot,...algebraics}, result:Record<string,FormulaEvaluation>={}; for(const rate of [...binding.rates].sort((a,b)=>a.rateRef.localeCompare(b.rateRef))) result[rate.rateRef]=evaluate(rate.formulaRef,values); return result; },
    validateConstraints(candidates){ for(const ref of binding.constraintRefs){ const constraint=binding.model.children.find(item=>item.symbol===ref); if(!constraint || constraint.kind!=="Constraint") simulationFail("INVALID_BINDING","CONSTRAINT","Constraint reference is invalid",{details:{ref}}); if(constraint.constraint_type==="range"){ const declaration=constraint.declaration as {min?:unknown;max?:unknown}; for(const symbol of constraint.refs){ const value=candidates[symbol]; if(value!==undefined && ((typeof declaration.min==="number" && value<declaration.min)||(typeof declaration.max==="number" && value>declaration.max))) return {ok:false as const,constraintRef:ref}; } } } return {ok:true as const}; }
  };
}
