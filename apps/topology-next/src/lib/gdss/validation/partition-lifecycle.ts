import type{HoldoutState,PartitionState}from"./partition-contracts";
const partitionEdges:Record<PartitionState,readonly PartitionState[]>={DRAFT:["REVIEW_REQUIRED"],REVIEW_REQUIRED:["DRAFT","APPROVED"],APPROVED:["PUBLISHED"],PUBLISHED:["SUPERSEDED","INVALIDATED"],SUPERSEDED:[],INVALIDATED:[]};
const holdoutEdges:Record<HoldoutState,readonly HoldoutState[]>={SEALED:["OPENED_FOR_EVALUATION","RETIRED","INVALIDATED"],OPENED_FOR_EVALUATION:["CONSUMED","INVALIDATED"],CONSUMED:["RETIRED","INVALIDATED"],RETIRED:[],INVALIDATED:[]};
export const canTransitionPartition=(from:PartitionState,to:PartitionState)=>partitionEdges[from].includes(to);
export const canTransitionHoldout=(from:HoldoutState,to:HoldoutState)=>holdoutEdges[from].includes(to);
