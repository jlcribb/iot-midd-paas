export interface Project {
  id: string;
  name: string;
  description: string | null;
  status: "draft" | "active" | "inactive" | "archived";
  parametric_control_enabled: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
