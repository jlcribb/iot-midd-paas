import { describe, expect, it } from "vitest";
import { buildGraph, normalizeNodeLayouts } from "@/components/topology/mappers";
import { resolveProjectTopologyStyles } from "@/components/topology/topology-style";
import type { ApiAsset, ApiSector } from "@/components/topology/types";

const sector: ApiSector = {
  id: "sector-1",
  project_id: "project-1",
  location_id: null,
  name: "Sector Norte",
  code: "SN",
  description: null,
  metadata: {}
};

const rootNode: ApiAsset = {
  id: "asset-1",
  project_id: "project-1",
  sector_id: "sector-1",
  parent_asset_id: null,
  asset_type: "programmable_node",
  subtype: "esp32",
  name: "Nodo principal",
  code: null,
  description: null,
  status: "active",
  metadata: {}
};

const sensor: ApiAsset = {
  id: "asset-2",
  project_id: "project-1",
  sector_id: "sector-1",
  parent_asset_id: "asset-1",
  asset_type: "sensor",
  subtype: "temperature",
  name: "Sensor T",
  code: null,
  description: null,
  status: "online",
  metadata: {}
};

describe("topology mappers", () => {
  it("applies project visual styles to sector and asset nodes", () => {
    const projectStyles = resolveProjectTopologyStyles({
      topology_node_styles: {
        sector: {
          shape: "hexagon",
          fillColor: "#112233",
          strokeColor: "#445566",
          textColor: "#ffffff"
        },
        assetTypes: {
          sensor: {
            shape: "star",
            fillColor: "#abcdef",
            strokeColor: "#123456",
            textColor: "#111111"
          }
        }
      }
    });

    const result = buildGraph({
      sectors: [sector],
      assets: [sensor],
      topologyLinks: [],
      nodeLayouts: [],
      linkLayouts: [],
      mode: "design",
      projectStyles,
      search: "",
      sectorFilters: [],
      typeFilters: [],
      statusFilters: [],
      showHierarchyEdges: true,
      showTopologyEdges: true
    });

    const sectorNode = result.nodes.find((node) => node.id === "sector:sector-1");
    const sensorNode = result.nodes.find((node) => node.id === "asset:asset-2");

    expect(sectorNode?.data).toMatchObject({
      shape: "hexagon",
      fillColor: "#112233",
      strokeColor: "#445566"
    });
    expect(sensorNode?.data).toMatchObject({
      shape: "star",
      fillColor: "#abcdef",
      strokeColor: "#123456"
    });
  });

  it("normalizes asset layouts to avoid overlap inside the same sector", () => {
    const normalized = normalizeNodeLayouts([sector], [rootNode, sensor], [
      {
        asset_id: null,
        sector_id: "sector-1",
        x: 0,
        y: 0,
        width: 520,
        height: 440,
        collapsed: false,
        hidden: false,
        z_index: 0,
        metadata: {}
      },
      {
        asset_id: "asset-1",
        sector_id: null,
        x: 40,
        y: 100,
        width: 196,
        height: 116,
        collapsed: false,
        hidden: false,
        z_index: 3,
        metadata: {}
      },
      {
        asset_id: "asset-2",
        sector_id: null,
        x: 40,
        y: 100,
        width: 196,
        height: 116,
        collapsed: false,
        hidden: false,
        z_index: 3,
        metadata: {}
      }
    ]);

    const rootLayout = normalized.find((layout) => layout.asset_id === "asset-1");
    const sensorLayout = normalized.find((layout) => layout.asset_id === "asset-2");

    expect(rootLayout).toBeTruthy();
    expect(sensorLayout).toBeTruthy();
    expect(sensorLayout?.x === rootLayout?.x && sensorLayout?.y === rootLayout?.y).toBe(false);
    expect(sensorLayout?.x).toBeGreaterThanOrEqual(34);
    expect(sensorLayout?.y).toBeGreaterThanOrEqual(94);
  });

  it("filters sectors and hides related nodes when sector filters are active", () => {
    const hiddenSector: ApiSector = {
      ...sector,
      id: "sector-2",
      name: "Sector Sur"
    };

    const hiddenAsset: ApiAsset = {
      ...sensor,
      id: "asset-3",
      sector_id: "sector-2",
      name: "Sensor Sur"
    };

    const result = buildGraph({
      sectors: [sector, hiddenSector],
      assets: [sensor, hiddenAsset],
      topologyLinks: [],
      nodeLayouts: [],
      linkLayouts: [],
      mode: "design",
      projectStyles: resolveProjectTopologyStyles({}),
      search: "",
      sectorFilters: ["sector-1"],
      typeFilters: [],
      statusFilters: [],
      showHierarchyEdges: true,
      showTopologyEdges: true
    });

    expect(result.nodes.find((node) => node.id === "sector:sector-1")?.hidden).toBe(false);
    expect(result.nodes.find((node) => node.id === "sector:sector-2")?.hidden).toBe(true);
    expect(result.nodes.find((node) => node.id === "asset:asset-2")?.hidden).toBe(false);
    expect(result.nodes.find((node) => node.id === "asset:asset-3")?.hidden).toBe(true);
  });
});
