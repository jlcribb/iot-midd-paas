import { NextResponse } from "next/server";
import type { ErrorPayload } from "@/lib/errors/app-error";

export interface SuccessResponse<T> {
  success: true;
  data: T;
}

export interface FailureResponse {
  success: false;
  error: ErrorPayload;
}

export function ok<T>(data: T, status = 200): NextResponse<SuccessResponse<T>> {
  return NextResponse.json(
    {
      success: true,
      data
    },
    { status }
  );
}

export function fail(error: ErrorPayload, status: number): NextResponse<FailureResponse> {
  return NextResponse.json(
    {
      success: false,
      error
    },
    { status }
  );
}
