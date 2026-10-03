import { describe, expect, it } from "vitest";
import { binary64Hex, canonicalAst, evaluateAst, expressionAstHash, parseExpression, tokenize } from "@/lib/gdss/expression";

describe("GDSS-002 parser and deterministic AST", () => {
  it("parses controlled numeric literals and identifiers", () => {
    for (const source of ["12","12.5","0.25","1e-3","2E6","flow_rate"]) expect(parseExpression(source).ast).toBeDefined();
    for (const source of [".5","1.","01","1e","1e+","0x10"]) expect(() => parseExpression(source)).toThrow();
  });
  it("implements approved unary and exponent precedence", () => {
    const unary=parseExpression("-2^2").ast;
    expect(unary).toMatchObject({kind:"UnaryExpression",operator:"-",operand:{kind:"BinaryExpression",operator:"^"}});
    expect(evaluateAst(unary,new Map())).toBe(-4);
    const right=parseExpression("2^3^2").ast;
    expect(right).toMatchObject({kind:"BinaryExpression",operator:"^",right:{kind:"BinaryExpression",operator:"^"}});
    expect(evaluateAst(right,new Map())).toBe(512);
  });
  it("retains spans and produces deterministic canonical AST hashes", () => {
    const first=parseExpression("abs(x) + pow(2, 3)"), second=parseExpression("abs(x) + pow(2, 3)");
    expect(first.ast.span).toEqual({start:0,end:18});
    expect(canonicalAst(first.ast)).toBe(canonicalAst(second.ast));
    expect(expressionAstHash(first.ast)).toMatch(/^[a-f0-9]{64}$/);
  });
  it("fails closed on unsupported language capabilities", () => {
    for(const source of ["Q = A * v","object.property","x[0]","constructor(1)","x > 0","2x","[1]","{x:1}"])
      expect(() => parseExpression(source)).toThrow();
  });
  it("distinguishes unsupported operators from other unsupported tokens", () => {
    for(const source of ["1=1","1%2","1<2"]) {
      try { parseExpression(source); throw Error("expected failure"); }
      catch(error) { expect((error as {diagnostic?:{code:string}}).diagnostic?.code).toBe("UNSUPPORTED_OPERATOR"); }
    }
  });
  it("enforces function allowlist and arity", () => {
    for(const source of ["abs()","sqrt(1,2)","min(1)","pow(2)","sin(1)"]) expect(() => parseExpression(source)).toThrow();
    expect(parseExpression("max(1,2,3)").ast).toMatchObject({kind:"FunctionCall",functionName:"max"});
  });
  it("canonicalizes binary64 negative zero and rejects non-finite identity", () => {
    expect(binary64Hex(-0)).toBe(binary64Hex(0));
    expect(() => binary64Hex(Infinity)).toThrow();
    expect(() => parseExpression("1e999")).toThrow();
  });
  it("enforces tokenizer limits during processing", () => {
    expect(() => tokenize("1+2+3",{profile:"GDSS_EXPR_LIMITS_V1",sourceLength:20,tokenCount:3,astDepth:64,astNodes:64,distinctSymbols:64,functionNesting:32,dependencyNodes:64,dependencyEdges:64,suppliedInputs:64,evaluatorOperations:64})).toThrow();
  });
});
