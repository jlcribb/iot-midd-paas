import type { PoolClient, QueryResult, QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";

export interface SqlExecutor {
  query<R extends QueryResultRow = QueryResultRow>(text: string, params?: readonly unknown[]): Promise<QueryResult<R>>;
}

export type TransactionRunner = <T>(fn: (tx: PoolClient) => Promise<T>) => Promise<T>;

export const withTransaction: TransactionRunner = async <T>(fn: (tx: PoolClient) => Promise<T>) => {
  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const result = await fn(client);
    await client.query("COMMIT");
    return result;
  } catch (error) {
    await client.query("ROLLBACK");
    throw error;
  } finally {
    client.release();
  }
};
