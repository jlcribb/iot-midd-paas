import type{DomainState,ProtocolState}from"./contracts";
export const protocolTransitionMap:Readonly<Record<ProtocolState,readonly ProtocolState[]>>={DRAFT:["REVIEW_REQUIRED"],REVIEW_REQUIRED:["DRAFT","APPROVED"],APPROVED:["SEALED"],SEALED:["SUPERSEDED","INVALIDATED"],SUPERSEDED:[],INVALIDATED:[]};
export const domainTransitionMap:Readonly<Record<DomainState,readonly DomainState[]>>={DRAFT:["APPROVED"],APPROVED:["SEALED"],SEALED:["SUPERSEDED","INVALIDATED"],SUPERSEDED:[],INVALIDATED:[]};
export const canTransitionProtocol=(from:ProtocolState,to:ProtocolState)=>protocolTransitionMap[from].includes(to);
export const canTransitionDomain=(from:DomainState,to:DomainState)=>domainTransitionMap[from].includes(to);
