export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: "draft" | "active" | "inactive" | "archived";
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
