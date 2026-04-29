export interface BuildUpdateOptions {
  startIndex?: number;
  casts?: Record<string, string>;
}

export interface BuiltUpdate {
  setClause: string;
  values: unknown[];
}

export function buildUpdateSet(data: Record<string, unknown>, options: BuildUpdateOptions = {}): BuiltUpdate {
  const keys = Object.keys(data);
  if (keys.length === 0) {
    return { setClause: "", values: [] };
  }

  const startIndex = options.startIndex ?? 1;
  const casts = options.casts ?? {};
  const assignments = keys.map((key, idx) => {
    const placeholder = `$${startIndex + idx}`;
    const cast = casts[key];
    if (cast) {
      return `${key} = ${placeholder}::${cast}`;
    }
    return `${key} = ${placeholder}`;
  });

  return {
    setClause: assignments.join(", "),
    values: keys.map((key) => data[key])
  };
}
