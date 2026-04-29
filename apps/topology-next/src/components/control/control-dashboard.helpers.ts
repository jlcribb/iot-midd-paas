import type {
  ControlAuditView,
  ControlRecommendationView,
  ControlStatusView
} from "@/lib/dto/control.dto";

export function formatControlTimestamp(value: string | null | undefined): string {
  if (!value) {
    return "Sin datos";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("es-AR", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(date);
}

export function getActivityBadgeClass(status: ControlStatusView["activity_status"]): string {
  switch (status) {
    case "active":
      return "status-badge status-active";
    case "stale":
      return "status-badge status-maintenance";
    default:
      return "status-badge status-inactive";
  }
}

export function getActivityLabel(status: ControlStatusView["activity_status"]): string {
  switch (status) {
    case "active":
      return "Activo";
    case "stale":
      return "Sin actividad reciente";
    default:
      return "Sin actividad";
  }
}

export function recommendationKey(item: ControlRecommendationView): string {
  return `${item.audit_id}:${item.event_id ?? "event"}`;
}

export function auditKey(item: ControlAuditView): string {
  return `${item.id}:${item.event_id ?? "event"}`;
}
