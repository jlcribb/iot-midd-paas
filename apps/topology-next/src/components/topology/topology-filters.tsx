"use client";

import type { ApiAsset, ApiSector } from "@/components/topology/types";

interface TopologyFiltersProps {
  sectors: ApiSector[];
  sectorFilters: string[];
  typeFilters: ApiAsset["asset_type"][];
  statusFilters: ApiAsset["status"][];
  onSectorFiltersChange: (value: string[]) => void;
  onTypeFiltersChange: (value: ApiAsset["asset_type"][]) => void;
  onStatusFiltersChange: (value: ApiAsset["status"][]) => void;
}

const ALL_TYPES: ApiAsset["asset_type"][] = [
  "programmable_node",
  "sensor",
  "actuator",
  "gateway",
  "relay_module",
  "camera",
  "power_unit"
];

const ALL_STATUS: ApiAsset["status"][] = [
  "online",
  "active",
  "offline",
  "inactive",
  "fault",
  "maintenance",
  "provisioning"
];

export function TopologyFilters(props: TopologyFiltersProps) {
  const hasActiveFilters =
    props.sectorFilters.length > 0 || props.typeFilters.length > 0 || props.statusFilters.length > 0;

  function toggleSector(value: string) {
    const next = props.sectorFilters.includes(value)
      ? props.sectorFilters.filter((item) => item !== value)
      : [...props.sectorFilters, value];
    props.onSectorFiltersChange(next);
  }

  function toggleType(value: ApiAsset["asset_type"]) {
    const next = props.typeFilters.includes(value)
      ? props.typeFilters.filter((item) => item !== value)
      : [...props.typeFilters, value];
    props.onTypeFiltersChange(next);
  }

  function toggleStatus(value: ApiAsset["status"]) {
    const next = props.statusFilters.includes(value)
      ? props.statusFilters.filter((item) => item !== value)
      : [...props.statusFilters, value];
    props.onStatusFiltersChange(next);
  }

  return (
    <div className="topology-filters">
      <div className="filter-group">
        <div className="filter-heading">
          <p className="filter-title">Sectores</p>
          {hasActiveFilters ? (
            <button
              type="button"
              className="filter-reset"
              onClick={() => {
                props.onSectorFiltersChange([]);
                props.onTypeFiltersChange([]);
                props.onStatusFiltersChange([]);
              }}
            >
              Limpiar
            </button>
          ) : null}
        </div>
        <div className="filter-chips">
          {props.sectors.map((sector) => (
            <button
              key={sector.id}
              type="button"
              className={props.sectorFilters.includes(sector.id) ? "chip chip-active" : "chip"}
              onClick={() => toggleSector(sector.id)}
            >
              {sector.name}
            </button>
          ))}
        </div>
      </div>
      <div className="filter-group">
        <p className="filter-title">Tipos</p>
        <div className="filter-chips">
          {ALL_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              className={props.typeFilters.includes(type) ? "chip chip-active" : "chip"}
              onClick={() => toggleType(type)}
            >
              {type}
            </button>
          ))}
        </div>
      </div>
      <div className="filter-group">
        <p className="filter-title">Estado</p>
        <div className="filter-chips">
          {ALL_STATUS.map((status) => (
            <button
              key={status}
              type="button"
              className={props.statusFilters.includes(status) ? "chip chip-active" : "chip"}
              onClick={() => toggleStatus(status)}
            >
              {status}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
