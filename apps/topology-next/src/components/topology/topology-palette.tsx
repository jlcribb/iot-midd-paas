"use client";

interface TopologyPaletteProps {
  disabled?: boolean;
  onCreateSector: () => void;
  onCreateNode: () => void;
  onCreateSensor: () => void;
  onCreateActuator: () => void;
}

export function TopologyPalette(props: TopologyPaletteProps) {
  return (
    <div className="topology-palette">
      <button type="button" className="btn btn-secondary" onClick={props.onCreateSector} disabled={props.disabled}>
        + Sector
      </button>
      <button type="button" className="btn btn-secondary" onClick={props.onCreateNode} disabled={props.disabled}>
        + Nodo
      </button>
      <button type="button" className="btn btn-secondary" onClick={props.onCreateSensor} disabled={props.disabled}>
        + Sensor hijo
      </button>
      <button type="button" className="btn btn-secondary" onClick={props.onCreateActuator} disabled={props.disabled}>
        + Actuador hijo
      </button>
    </div>
  );
}
