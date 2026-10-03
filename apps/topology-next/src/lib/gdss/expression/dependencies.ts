import { fail } from "./diagnostics";
import { assertLimit, DEFAULT_EXPRESSION_LIMITS, type ExpressionLimits } from "./limits";

export interface FormulaDependency { formula: string; output: string; inputs: readonly string[] }
export interface DependencyGraph {
  nodes: readonly string[];
  directDependencies: Readonly<Record<string,readonly string[]>>;
  transitiveDependencies: Readonly<Record<string,readonly string[]>>;
  stronglyConnectedComponents: readonly (readonly string[])[];
  topologicalOrder?: readonly string[];
}

export function buildDependencyGraph(records: readonly FormulaDependency[], limits: ExpressionLimits = DEFAULT_EXPRESSION_LIMITS): DependencyGraph {
  const adjacency = new Map<string,Set<string>>();
  const producers = new Map<string,string>();
  for (const record of records) {
    const prior = producers.get(record.output);
    if (prior && prior !== record.formula) fail("AMBIGUOUS_SYMBOL", "SYMBOL_RESOLVED", "Multiple formulas produce the same symbol", { symbol: record.output, actual: [prior,record.formula] });
    producers.set(record.output,record.formula);
    adjacency.set(record.output,new Set(record.inputs));
    for (const input of record.inputs) if (!adjacency.has(input)) adjacency.set(input,new Set());
  }
  const nodes = [...adjacency.keys()].sort();
  const edgeCount = [...adjacency.values()].reduce((count,edges) => count + edges.size,0);
  assertLimit(nodes.length,limits.dependencyNodes,"dependency graph nodes","SYMBOL_RESOLVED");
  assertLimit(edgeCount,limits.dependencyEdges,"dependency graph edges","SYMBOL_RESOLVED");
  const index = new Map<string,number>(), low = new Map<string,number>(), stack: string[] = [], onStack = new Set<string>(), components: string[][] = [];
  let cursor = 0;
  const strong = (node: string) => {
    index.set(node,cursor); low.set(node,cursor); cursor += 1; stack.push(node); onStack.add(node);
    for (const next of [...(adjacency.get(node) ?? [])].sort()) {
      if (!index.has(next)) { strong(next); low.set(node,Math.min(low.get(node)!,low.get(next)!)); }
      else if (onStack.has(next)) low.set(node,Math.min(low.get(node)!,index.get(next)!));
    }
    if (low.get(node) === index.get(node)) {
      const component: string[] = []; let item: string;
      do { item = stack.pop()!; onStack.delete(item); component.push(item); } while (item !== node);
      components.push(component.sort());
    }
  };
  nodes.forEach(node => { if (!index.has(node)) strong(node); });
  components.sort((a,b) => a[0].localeCompare(b[0]));
  const cyclic = components.some(c => c.length > 1 || adjacency.get(c[0])?.has(c[0]));
  const transitive: Record<string,string[]> = {};
  for (const node of nodes) {
    const seen = new Set<string>(); const visit = (current: string) => { for (const next of adjacency.get(current) ?? []) if (!seen.has(next)) { seen.add(next); visit(next); } };
    visit(node); transitive[node] = [...seen].sort();
  }
  let topologicalOrder: string[] | undefined;
  if (!cyclic) {
    const visited = new Set<string>(), order: string[] = [];
    const visit = (node: string) => { if (visited.has(node)) return; visited.add(node); for (const next of [...(adjacency.get(node) ?? [])].sort()) visit(next); order.push(node); };
    nodes.forEach(visit); topologicalOrder = order;
  }
  return {
    nodes,
    directDependencies: Object.fromEntries(nodes.map(node => [node,[...(adjacency.get(node) ?? [])].sort()])),
    transitiveDependencies: transitive,
    stronglyConnectedComponents: components,
    topologicalOrder
  };
}

export function assertAcyclic(graph: DependencyGraph) {
  const cycle = graph.stronglyConnectedComponents.find(component => component.length > 1 || graph.directDependencies[component[0]]?.includes(component[0]));
  if (cycle) fail("CYCLIC_DEPENDENCY_REQUIRES_DYNAMIC_SEMANTICS", "SYMBOL_RESOLVED", "Computational cycle requires future dynamic semantics", { actual: cycle });
}
