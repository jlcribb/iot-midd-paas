import { describe, expect, it } from "vitest";
import {
  analyzeAst, assertAcyclic, buildDependencyGraph, DIMENSIONLESS, divideDimensions,
  evaluateAst, assertKnownDimension, catalogUnit, fromCanonical, multiplyDimensions,
  parseExpression, powerDimension, sqrtDimension, toCanonical
} from "@/lib/gdss/expression";

describe("GDSS-002 dimensional, function and dependency semantics", () => {
  const ast=(source:string)=>parseExpression(source).ast;
  it("evaluates the exact allowlisted functions", () => {
    const cases:[[string,number],...[string,number][]]=[["abs(-2)",2],["min(3,1,2)",1],["max(3,1,2)",3],["sqrt(9)",3],["exp(0)",1],["ln(1)",0],["log10(100)",2],["pow(2,3)",8]];
    for(const [source,value] of cases) { const parsed=ast(source); analyzeAst(parsed,new Map()); expect(evaluateAst(parsed,new Map())).toBeCloseTo(value); }
  });
  it("fails closed on numeric domains and division by either zero", () => {
    for(const source of ["1/0","0/0","sqrt(-1)","ln(0)","ln(-1)","pow(-2,0.5)","exp(10000)"]) {
      const parsed=ast(source); analyzeAst(parsed,new Map()); expect(() => evaluateAst(parsed,new Map())).toThrow();
    }
  });
  it("implements integer seven-vector algebra without rounding", () => {
    expect(multiplyDimensions([1,0,0,0,0,0,0],[0,0,-1,0,0,0,0])).toEqual([1,0,-1,0,0,0,0]);
    expect(divideDimensions([1,0,0,0,0,0,0],[0,0,1,0,0,0,0])).toEqual([1,0,-1,0,0,0,0]);
    expect(powerDimension([1,0,0,0,0,0,0],2)).toEqual([2,0,0,0,0,0,0]);
    expect(sqrtDimension([2,0,0,0,0,0,0])).toEqual([1,0,0,0,0,0,0]);
    expect(() => sqrtDimension([1,0,0,0,0,0,0])).toThrow();
    expect(() => powerDimension([1,0,0,0,0,0,0],0.5)).toThrow();
    expect(assertKnownDimension([0,0,0,0,0,0,0])).toEqual(DIMENSIONLESS);
    expect(() => assertKnownDimension(undefined)).toThrow();
  });
  it("keeps unit identity separate from dimension and converts by catalog revision", () => {
    const centimeter=catalogUnit({key:"centimeter",revision:1}), meter=catalogUnit({key:"meter",revision:1});
    expect(centimeter.dimension).toEqual(meter.dimension);
    expect(fromCanonical(toCanonical(123,centimeter,"INTERVAL"),meter,"INTERVAL")).toBeCloseTo(1.23);
    expect(() => catalogUnit({key:"centimeter",revision:2})).toThrow();
  });
  it("requires dimensionless inputs for exponential and logarithmic functions", () => {
    const symbols=new Map([["x",{value:1,dimension:[1,0,0,0,0,0,0] as typeof DIMENSIONLESS}]]);
    expect(() => analyzeAst(ast("exp(x)"),symbols)).toThrow();
  });
  it("accepts sqrt only when dimensional exponents remain integral", () => {
    const squared=new Map([["x",{value:9,dimension:[2,0,0,0,0,0,0] as typeof DIMENSIONLESS}]]);
    expect(analyzeAst(ast("sqrt(x)"),squared).dimension).toEqual([1,0,0,0,0,0,0]);
    const linear=new Map([["x",{value:9,dimension:[1,0,0,0,0,0,0] as typeof DIMENSIONLESS}]]);
    expect(() => analyzeAst(ast("sqrt(x)"),linear)).toThrow();
  });
  it("derives deterministic direct/transitive dependencies", () => {
    const graph=buildDependencyGraph([{formula:"fa",output:"a",inputs:["b","c","b"]},{formula:"fb",output:"b",inputs:["d"]}]);
    expect(graph.directDependencies.a).toEqual(["b","c"]);
    expect(graph.transitiveDependencies.a).toEqual(["b","c","d"]);
    expect(graph.topologicalOrder).toBeDefined();
  });
  it("diagnoses cycles without solving or declaring scientific invalidity", () => {
    const graph=buildDependencyGraph([{formula:"fa",output:"a",inputs:["b"]},{formula:"fb",output:"b",inputs:["a"]}]);
    expect(graph.topologicalOrder).toBeUndefined();
    expect(() => assertAcyclic(graph)).toThrow(/dynamic semantics/);
  });
});
