"use client";

import type { ApiAsset } from "@/components/topology/types";

export type NodeShape = "rectangle" | "circle" | "diamond" | "hexagon" | "octagon" | "star";

export interface TopologyNodeVisualStyle {
  shape: NodeShape;
  fillColor: string;
  strokeColor: string;
  textColor: string;
}

export interface ProjectTopologyStyles {
  sector: TopologyNodeVisualStyle;
  assetTypes: Record<ApiAsset["asset_type"], TopologyNodeVisualStyle>;
}

export const NODE_SHAPE_OPTIONS: Array<{ value: NodeShape; label: string }> = [
  { value: "rectangle", label: "Rectángulo" },
  { value: "circle", label: "Círculo" },
  { value: "diamond", label: "Rombo" },
  { value: "hexagon", label: "Hexágono" },
  { value: "octagon", label: "Octágono" },
  { value: "star", label: "Estrella" }
];

export const ASSET_TYPE_LABELS: Record<ApiAsset["asset_type"], string> = {
  programmable_node: "Nodo programable",
  sensor: "Sensor",
  actuator: "Actuador",
  gateway: "Gateway",
  relay_module: "Módulo relay",
  camera: "Cámara",
  power_unit: "Unidad de energía"
};

const DEFAULT_PROJECT_TOPOLOGY_STYLES: ProjectTopologyStyles = {
  sector: {
    shape: "rectangle",
    fillColor: "#e8eef7",
    strokeColor: "#94a3b8",
    textColor: "#0f172a"
  },
  assetTypes: {
    programmable_node: {
      shape: "hexagon",
      fillColor: "#eef4fb",
      strokeColor: "#64748b",
      textColor: "#0f172a"
    },
    sensor: {
      shape: "circle",
      fillColor: "#edf8f1",
      strokeColor: "#65a30d",
      textColor: "#14532d"
    },
    actuator: {
      shape: "diamond",
      fillColor: "#fdf0f0",
      strokeColor: "#dc6b6b",
      textColor: "#7f1d1d"
    },
    gateway: {
      shape: "octagon",
      fillColor: "#fdf6e6",
      strokeColor: "#c28a2c",
      textColor: "#78350f"
    },
    relay_module: {
      shape: "rectangle",
      fillColor: "#f4effc",
      strokeColor: "#8b5cf6",
      textColor: "#4c1d95"
    },
    camera: {
      shape: "star",
      fillColor: "#f8eef8",
      strokeColor: "#c061c7",
      textColor: "#86198f"
    },
    power_unit: {
      shape: "hexagon",
      fillColor: "#ebf7f6",
      strokeColor: "#2f8f88",
      textColor: "#134e4a"
    }
  }
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalizeColor(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback;
  const trimmed = value.trim();
  return /^#[0-9a-fA-F]{6}$/.test(trimmed) ? trimmed : fallback;
}

function normalizeShape(value: unknown, fallback: NodeShape): NodeShape {
  return NODE_SHAPE_OPTIONS.some((option) => option.value === value) ? (value as NodeShape) : fallback;
}

function normalizeVisualStyle(value: unknown, fallback: TopologyNodeVisualStyle): TopologyNodeVisualStyle {
  if (!isRecord(value)) return fallback;
  return {
    shape: normalizeShape(value.shape, fallback.shape),
    fillColor: normalizeColor(value.fillColor, fallback.fillColor),
    strokeColor: normalizeColor(value.strokeColor, fallback.strokeColor),
    textColor: normalizeColor(value.textColor, fallback.textColor)
  };
}

export function getDefaultProjectTopologyStyles(): ProjectTopologyStyles {
  return {
    sector: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.sector },
    assetTypes: {
      programmable_node: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.programmable_node },
      sensor: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.sensor },
      actuator: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.actuator },
      gateway: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.gateway },
      relay_module: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.relay_module },
      camera: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.camera },
      power_unit: { ...DEFAULT_PROJECT_TOPOLOGY_STYLES.assetTypes.power_unit }
    }
  };
}

export function resolveProjectTopologyStyles(metadata: Record<string, unknown> | null | undefined): ProjectTopologyStyles {
  const defaults = getDefaultProjectTopologyStyles();
  const styleMetadata = isRecord(metadata?.topology_node_styles) ? metadata.topology_node_styles : {};
  const assetTypeMetadata = isRecord(styleMetadata.assetTypes) ? styleMetadata.assetTypes : {};

  return {
    sector: normalizeVisualStyle(styleMetadata.sector, defaults.sector),
    assetTypes: {
      programmable_node: normalizeVisualStyle(assetTypeMetadata.programmable_node, defaults.assetTypes.programmable_node),
      sensor: normalizeVisualStyle(assetTypeMetadata.sensor, defaults.assetTypes.sensor),
      actuator: normalizeVisualStyle(assetTypeMetadata.actuator, defaults.assetTypes.actuator),
      gateway: normalizeVisualStyle(assetTypeMetadata.gateway, defaults.assetTypes.gateway),
      relay_module: normalizeVisualStyle(assetTypeMetadata.relay_module, defaults.assetTypes.relay_module),
      camera: normalizeVisualStyle(assetTypeMetadata.camera, defaults.assetTypes.camera),
      power_unit: normalizeVisualStyle(assetTypeMetadata.power_unit, defaults.assetTypes.power_unit)
    }
  };
}
