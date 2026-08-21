import { createHash } from "node:crypto";

export type CanonicalJson = null | boolean | number | string | CanonicalJson[] | { [key: string]: CanonicalJson };

function normalize(value: unknown): CanonicalJson {
  if (value === null || typeof value === "boolean" || typeof value === "string") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("Canonical snapshots do not permit non-finite numbers");
    return Object.is(value, -0) ? 0 : value;
  }
  if (value instanceof Date) {
    if (Number.isNaN(value.getTime())) throw new TypeError("Canonical snapshots do not permit invalid dates");
    return value.toISOString();
  }
  if (Array.isArray(value)) return value.map(normalize);
  if (value && typeof value === "object") {
    const result: Record<string, CanonicalJson> = {};
    for (const key of Object.keys(value).sort()) {
      const entry = (value as Record<string, unknown>)[key];
      if (entry !== undefined) result[key] = normalize(entry);
    }
    return result;
  }
  throw new TypeError(`Canonical snapshots do not support ${typeof value}`);
}

function stringify(value: CanonicalJson): string {
  if (value === null) return "null";
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number" || typeof value === "boolean") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stringify).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stringify(value[key])}`).join(",")}}`;
}

export function canonicalSerialize(value: unknown): string {
  return stringify(normalize(value));
}

/** A detached JSON-only value with sorted object keys and no undefined fields. */
export function canonicalClone<T>(value: T): T {
  return JSON.parse(canonicalSerialize(value)) as T;
}

export function sha256Canonical(value: unknown): string {
  return createHash("sha256").update(canonicalSerialize(value), "utf8").digest("hex");
}

export function normalizeTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new TypeError("Snapshot timestamp must be a valid ISO-8601 instant");
  return date.toISOString();
}

export function experimentFingerprint(componentHashes: {
  policy_snapshot_hash: string;
  topology_snapshot_hash: string;
  dataset_snapshot_hash: string;
  configuration_snapshot_hash: string;
}): string {
  return sha256Canonical({ schema_version: 1, component_hashes: componentHashes });
}
