import { Pool } from "pg";

const sslEnabled = process.env.DB_SSL === "true";

export const pool = new Pool({
  host: process.env.DB_HOST ?? "localhost",
  port: Number(process.env.DB_PORT ?? 5432),
  database: process.env.DB_NAME ?? "iot_middleware",
  user: process.env.DB_USER ?? "iot_user",
  password: process.env.DB_PASSWORD ?? "iot_password_2024",
  ssl: sslEnabled ? { rejectUnauthorized: false } : undefined,
  max: 20
});
