export interface PaginationInput {
  limit?: number;
  offset?: number;
}

export interface PaginationResult {
  limit: number;
  offset: number;
}

export function parsePagination(input: PaginationInput): PaginationResult {
  const rawLimit = input.limit ?? 100;
  const rawOffset = input.offset ?? 0;

  const limit = Math.min(Math.max(rawLimit, 1), 500);
  const offset = Math.max(rawOffset, 0);

  return { limit, offset };
}
