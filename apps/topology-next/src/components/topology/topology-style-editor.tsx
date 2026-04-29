"use client";

import type { ApiAsset, ApiProject } from "@/components/topology/types";
import {
  ASSET_TYPE_LABELS,
  NODE_SHAPE_OPTIONS,
  type ProjectTopologyStyles
} from "@/components/topology/topology-style";

interface TopologyStyleEditorProps {
  project: ApiProject | null;
  mode: "design" | "operation";
  styles: ProjectTopologyStyles;
  isDirty: boolean;
  onChange: (styles: ProjectTopologyStyles) => void;
}

type StyleKey = "sector" | ApiAsset["asset_type"];

export function TopologyStyleEditor(props: TopologyStyleEditorProps) {
  function updateStyle(styleKey: StyleKey, field: "shape" | "fillColor" | "strokeColor" | "textColor", value: string) {
    const nextStyles: ProjectTopologyStyles =
      styleKey === "sector"
        ? {
            ...props.styles,
            sector: {
              ...props.styles.sector,
              [field]: value
            }
          }
        : {
            ...props.styles,
            assetTypes: {
              ...props.styles.assetTypes,
              [styleKey]: {
                ...props.styles.assetTypes[styleKey],
                [field]: value
              }
            }
          };

    props.onChange(nextStyles);
  }

  function getStyle(styleKey: StyleKey) {
    return styleKey === "sector" ? props.styles.sector : props.styles.assetTypes[styleKey];
  }

  const rows: Array<{ key: StyleKey; label: string }> = [
    { key: "sector", label: "Sector" },
    { key: "programmable_node", label: ASSET_TYPE_LABELS.programmable_node },
    { key: "sensor", label: ASSET_TYPE_LABELS.sensor },
    { key: "actuator", label: ASSET_TYPE_LABELS.actuator },
    { key: "gateway", label: ASSET_TYPE_LABELS.gateway },
    { key: "relay_module", label: ASSET_TYPE_LABELS.relay_module },
    { key: "camera", label: ASSET_TYPE_LABELS.camera },
    { key: "power_unit", label: ASSET_TYPE_LABELS.power_unit }
  ];

  return (
    <section className="panel-block">
      <div className="panel-heading-inline">
        <h2>Estilo por tipo</h2>
        {props.project ? <span className="panel-muted">{props.project.name}</span> : null}
      </div>

      <p className="panel-note">
        Los cambios se aplican al instante en el canvas y se guardan junto con el workspace.
        {props.isDirty ? " Hay cambios pendientes." : " Sin cambios pendientes."}
      </p>

      <div className="style-editor-list">
        {rows.map((row) => {
          const style = getStyle(row.key);
          return (
            <div key={row.key} className="style-editor-card">
              <div className="style-editor-title-row">
                <strong>{row.label}</strong>
                <span
                  className="style-preview-dot"
                  style={{ backgroundColor: style.fillColor, borderColor: style.strokeColor }}
                />
              </div>

              <label className="input-label">
                Forma
                <select
                  className="input-select full"
                  value={style.shape}
                  onChange={(event) => updateStyle(row.key, "shape", event.target.value)}
                  disabled={props.mode !== "design"}
                >
                  {NODE_SHAPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <div className="style-editor-colors">
                <label className="input-label">
                  Relleno
                  <input
                    className="input-color"
                    type="color"
                    value={style.fillColor}
                    onChange={(event) => updateStyle(row.key, "fillColor", event.target.value)}
                    disabled={props.mode !== "design"}
                  />
                </label>
                <label className="input-label">
                  Línea
                  <input
                    className="input-color"
                    type="color"
                    value={style.strokeColor}
                    onChange={(event) => updateStyle(row.key, "strokeColor", event.target.value)}
                    disabled={props.mode !== "design"}
                  />
                </label>
                <label className="input-label">
                  Texto
                  <input
                    className="input-color"
                    type="color"
                    value={style.textColor}
                    onChange={(event) => updateStyle(row.key, "textColor", event.target.value)}
                    disabled={props.mode !== "design"}
                  />
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

