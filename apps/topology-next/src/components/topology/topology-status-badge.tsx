"use client";

interface TopologyStatusBadgeProps {
  status: string;
}

const STATUS_CLASS: Record<string, string> = {
  online: "status-badge status-online",
  active: "status-badge status-active",
  offline: "status-badge status-offline",
  inactive: "status-badge status-inactive",
  fault: "status-badge status-fault",
  maintenance: "status-badge status-maintenance",
  provisioning: "status-badge status-provisioning",
  retired: "status-badge status-retired",
  planned: "status-badge status-planned"
};

export function TopologyStatusBadge({ status }: TopologyStatusBadgeProps) {
  return <span className={STATUS_CLASS[status] ?? "status-badge"}>{status}</span>;
}
