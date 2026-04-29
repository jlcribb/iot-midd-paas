import type { DatabaseError } from "pg";
import { AppError } from "@/lib/errors/app-error";
import { ConflictError, InternalError, ValidationError } from "@/lib/errors/domain-errors";

function getPgErrorCode(error: unknown): string | undefined {
  if (typeof error !== "object" || error === null) {
    return undefined;
  }
  return (error as DatabaseError).code;
}

function getPgMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected database error";
}

export function mapDatabaseError(error: unknown): AppError {
  if (error instanceof AppError) {
    return error;
  }

  const code = getPgErrorCode(error);
  const message = getPgMessage(error);

  switch (code) {
    case "23505":
      return new ConflictError(message);
    case "23503":
      return new ConflictError(message);
    case "23514":
      return new ConflictError(message);
    case "22P02":
      return new ValidationError(message);
    default:
      return new InternalError(message);
  }
}
