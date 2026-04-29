import type { QueryResultRow } from "pg";
import { pool } from "@/lib/db/pool";
import type { SqlExecutor } from "@/lib/db/tx";
import { buildUpdateSet } from "@/lib/db/sql";
import type { Location } from "@/lib/dto/location.dto";
import type { ILocationRepository } from "@/lib/repositories/contracts";
import type { CreateLocationInput, UpdateLocationInput } from "@/lib/validators/location.schemas";

function mapLocation(row: QueryResultRow): Location {
  return {
    id: String(row.id),
    name: String(row.name),
    description: row.description as string | null,
    latitude: row.latitude === null ? null : Number(row.latitude),
    longitude: row.longitude === null ? null : Number(row.longitude),
    altitude: row.altitude === null ? null : Number(row.altitude),
    accuracy_meters: row.accuracy_meters === null ? null : Number(row.accuracy_meters),
    country: row.country as string | null,
    province: row.province as string | null,
    city: row.city as string | null,
    address_text: row.address_text as string | null,
    building: row.building as string | null,
    floor: row.floor as string | null,
    zone: row.zone as string | null,
    rack: row.rack as string | null,
    position: row.position as string | null,
    metadata: (row.metadata ?? {}) as Record<string, unknown>,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at)
  };
}

export class LocationRepository implements ILocationRepository {
  constructor(private readonly db: SqlExecutor = pool) {}

  async create(input: CreateLocationInput): Promise<Location> {
    const result = await this.db.query(
      `
      INSERT INTO locations (
        name, description, latitude, longitude, altitude, accuracy_meters,
        country, province, city, address_text, building, floor, zone, rack, position, metadata
      )
      VALUES (
        $1, $2, $3, $4, $5, $6,
        $7, $8, $9, $10, $11, $12, $13, $14, $15, $16::jsonb
      )
      RETURNING *
      `,
      [
        input.name,
        input.description ?? null,
        input.latitude ?? null,
        input.longitude ?? null,
        input.altitude ?? null,
        input.accuracy_meters ?? null,
        input.country ?? null,
        input.province ?? null,
        input.city ?? null,
        input.address_text ?? null,
        input.building ?? null,
        input.floor ?? null,
        input.zone ?? null,
        input.rack ?? null,
        input.position ?? null,
        JSON.stringify(input.metadata ?? {})
      ]
    );
    return mapLocation(result.rows[0]);
  }

  async findById(id: string): Promise<Location | null> {
    const result = await this.db.query("SELECT * FROM locations WHERE id = $1::uuid", [id]);
    return result.rows[0] ? mapLocation(result.rows[0]) : null;
  }

  async findAll(): Promise<Location[]> {
    const result = await this.db.query("SELECT * FROM locations ORDER BY created_at DESC");
    return result.rows.map(mapLocation);
  }

  async update(id: string, input: UpdateLocationInput): Promise<Location | null> {
    const payload: Record<string, unknown> = {};
    for (const key of [
      "name",
      "description",
      "latitude",
      "longitude",
      "altitude",
      "accuracy_meters",
      "country",
      "province",
      "city",
      "address_text",
      "building",
      "floor",
      "zone",
      "rack",
      "position"
    ] as const) {
      if (input[key] !== undefined) {
        payload[key] = input[key] ?? null;
      }
    }
    if (input.metadata !== undefined) {
      payload.metadata = JSON.stringify(input.metadata ?? {});
    }

    if (Object.keys(payload).length === 0) {
      return this.findById(id);
    }

    const { setClause, values } = buildUpdateSet(payload, {
      startIndex: 2,
      casts: {
        metadata: "jsonb"
      }
    });

    const result = await this.db.query(`UPDATE locations SET ${setClause} WHERE id = $1::uuid RETURNING *`, [id, ...values]);
    return result.rows[0] ? mapLocation(result.rows[0]) : null;
  }
}
