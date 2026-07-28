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
      <button type="button" className="palette-action" onClick={props.onCreateSector} disabled={props.disabled}>
        <strong>+ Sector</strong>
        <span>Crea una agrupación para organizar activos.</span>
      </button>
      <button type="button" className="palette-action" onClick={props.onCreateNode} disabled={props.disabled}>
        <strong>+ Nodo</strong>
        <span>Agrega un programmable node al sector actual.</span>
      </button>
      <button type="button" className="palette-action" onClick={props.onCreateSensor} disabled={props.disabled}>
        <strong>+ Sensor hijo</strong>
        <span>Usa el nodo seleccionado como padre.</span>
      </button>
      <button type="button" className="palette-action" onClick={props.onCreateActuator} disabled={props.disabled}>
        <strong>+ Actuador hijo</strong>
        <span>Asocia una salida controlable al nodo elegido.</span>
      </button>
    </div>
  );
}
