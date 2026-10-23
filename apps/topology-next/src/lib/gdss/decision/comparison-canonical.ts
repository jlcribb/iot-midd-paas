import {canonicalValidationJson,validationHash} from "@/lib/gdss/validation";
import {comparisonAssemblyInputSchema,criterionDefinitionInputSchema,type ComparisonAssemblyInput,type CriterionDefinitionInput} from "./comparison-contracts";

const omitIdentity=<T extends {idempotencyKey:string}>(value:T)=>{const {idempotencyKey:_,...content}=value;return content;};
export function canonicalCriterion(raw:unknown):CriterionDefinitionInput{const value=criterionDefinitionInputSchema.parse(raw);return {...value,requiredInputs:[...value.requiredInputs].sort((a,b)=>`${a.target}:${a.horizon}:${a.quantity}:${a.unit.key}:${a.unit.revision}`.localeCompare(`${b.target}:${b.horizon}:${b.quantity}:${b.unit.key}:${b.unit.revision}`))};}
export const canonicalCriterionContent=(raw:unknown)=>omitIdentity(canonicalCriterion(raw));
export const criterionDefinitionHash=(raw:unknown)=>validationHash("midd:gdss:decision-criterion:v1",canonicalCriterionContent(raw));
export function canonicalComparison(raw:unknown):ComparisonAssemblyInput{const value=comparisonAssemblyInputSchema.parse(raw);return {...value,alternativeVersionIds:[...value.alternativeVersionIds].sort(),criterionVersionIds:[...value.criterionVersionIds].sort(),criterionEvaluationIds:[...value.criterionEvaluationIds].sort(),constraintEvaluationIds:[...value.constraintEvaluationIds].sort()};}
export const canonicalComparisonContent=(raw:unknown)=>omitIdentity(canonicalComparison(raw));
export const comparisonSetHash=(raw:unknown)=>validationHash("midd:gdss:decision-comparison:v1",canonicalComparisonContent(raw));
export const criterionResultHash=(raw:unknown)=>validationHash("midd:gdss:criterion-result:v1",raw);
export const constraintResultHash=(raw:unknown)=>validationHash("midd:gdss:constraint-result:v1",raw);
export const dominanceRelationHash=(raw:unknown)=>validationHash("midd:gdss:dominance-relation:v1",raw);
export const tradeoffAssessmentHash=(raw:unknown)=>validationHash("midd:gdss:tradeoff-assessment:v1",raw);
export {canonicalValidationJson as canonicalComparisonJson};
