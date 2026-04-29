import { NextResponse } from "next/server";
import { ZodError } from "zod";
import { mapDatabaseError } from "@/lib/errors/db-error-mapper";
import { AppError } from "@/lib/errors/app-error";
import { ValidationError } from "@/lib/errors/domain-errors";
import { fail } from "@/lib/http/response";

export type AsyncRouteHandler<TArgs extends unknown[] = []> = (...args: TArgs) => Promise<NextResponse>;

export function withRouteErrorHandling<TArgs extends unknown[]>(handler: AsyncRouteHandler<TArgs>): AsyncRouteHandler<TArgs> {
  return async (...args: TArgs): Promise<NextResponse> => {
    try {
      return await handler(...args);
    } catch (error) {
      console.error("[api-route-error]", error);

      if (error instanceof ZodError) {
        const appError = new ValidationError("Invalid payload", error.issues);
        return fail(appError.toPayload(), appError.status);
      }

      const mapped = mapDatabaseError(error);
      if (mapped instanceof AppError) {
        return fail(mapped.toPayload(), mapped.status);
      }

      return fail(
        {
          code: "INTERNAL_ERROR",
          message: "Unexpected internal error"
        },
        500
      );
    }
  };
}
