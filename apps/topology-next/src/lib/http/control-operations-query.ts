import { ValidationError } from "@/lib/errors/domain-errors";

export function parseOperationsPage(searchParams: URLSearchParams) {
  const limitRaw = searchParams.get("limit");
  const offsetRaw = searchParams.get("offset");
  const limit = limitRaw === null ? undefined : Number(limitRaw);
  const offset = offsetRaw === null ? undefined : Number(offsetRaw);
  if (limitRaw !== null && !Number.isFinite(limit)) throw new ValidationError("limit must be a number");
  if (offsetRaw !== null && !Number.isFinite(offset)) throw new ValidationError("offset must be a number");
  return { limit, offset };
}

export function optionalQuery(searchParams: URLSearchParams, name: string) {
  return searchParams.get(name)?.trim() || undefined;
}
