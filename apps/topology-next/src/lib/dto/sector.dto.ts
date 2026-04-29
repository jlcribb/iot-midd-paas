export interface Sector {
  id: string;
  project_id: string;
  location_id: string | null;
  name: string;
  code: string | null;
  description: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
