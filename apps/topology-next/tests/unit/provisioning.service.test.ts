import { describe, expect, it, vi } from "vitest";
import type { PoolClient } from "pg";
import { ProvisioningService } from "@/lib/services/provisioning.service";
import type { TransactionRunner } from "@/lib/db/tx";
import type { BootstrapNodeWithDevicesInput } from "@/lib/validators/topology.schemas";

const bootstrapInput: BootstrapNodeWithDevicesInput = {
  project_id: "11111111-1111-4111-8111-111111111111",
  sector: {
    name: "Tanque Norte",
    code: "TN-1",
    description: null,
    metadata: {}
  },
  node_location: undefined,
  node: {
    subtype: "esp32",
    name: "ESP32 Principal",
    code: "NODE-1",
    description: null,
    status: "active",
    metadata: {}
  },
  devices: [
    {
      asset_type: "sensor",
      subtype: "ultrasonic",
      name: "Sensor Nivel",
      code: "SEN-1",
      description: null,
      status: "active",
      metadata: {}
    },
    {
      asset_type: "actuator",
      subtype: "pump",
      name: "Bomba",
      code: "ACT-1",
      description: null,
      status: "active",
      metadata: {}
    }
  ],
  create_topology_links: true
};

describe("ProvisioningService", () => {
  it("bootstrap transaction succeeds and returns created ids", async () => {
    const txRunner: TransactionRunner = async (fn) => fn({} as PoolClient);

    const sectorServiceCreate = vi.fn().mockResolvedValue({ id: "sector-1" });
    const assetServiceCreate = vi
      .fn()
      .mockResolvedValueOnce({ id: "node-1", asset_type: "programmable_node" })
      .mockResolvedValueOnce({ id: "sensor-1", asset_type: "sensor" })
      .mockResolvedValueOnce({ id: "actuator-1", asset_type: "actuator" });
    const topologyServiceCreate = vi
      .fn()
      .mockResolvedValueOnce({ id: "link-contains" })
      .mockResolvedValueOnce({ id: "link-reads" })
      .mockResolvedValueOnce({ id: "link-controls" });

    const service = new ProvisioningService({
      transactionRunner: txRunner,
      contextFactory: (() => ({
        projectRepo: {
          findById: vi.fn().mockResolvedValue({ id: bootstrapInput.project_id })
        },
        sectorRepo: {
          findById: vi.fn()
        },
        locationRepo: {
          create: vi.fn()
        },
        assetRepo: {},
        topologyRepo: {},
        sectorService: {
          create: sectorServiceCreate
        },
        assetService: {
          create: assetServiceCreate
        },
        topologyService: {
          create: topologyServiceCreate
        }
      })) as never
    });

    const result = await service.bootstrapNodeWithDevices(bootstrapInput);

    expect(result.project_id).toBe(bootstrapInput.project_id);
    expect(result.sector_id).toBe("sector-1");
    expect(result.node_id).toBe("node-1");
    expect(result.device_ids).toEqual(["sensor-1", "actuator-1"]);
    expect(result.topology_link_ids).toEqual(["link-contains", "link-reads", "link-controls"]);
    expect(sectorServiceCreate).toHaveBeenCalledTimes(1);
  });

  it("bootstrap transaction triggers rollback path when a step fails", async () => {
    const transactionState: string[] = [];
    const txRunner: TransactionRunner = async (fn) => {
      transactionState.push("begin");
      try {
        const result = await fn({} as PoolClient);
        transactionState.push("commit");
        return result;
      } catch (error) {
        transactionState.push("rollback");
        throw error;
      }
    };

    const service = new ProvisioningService({
      transactionRunner: txRunner,
      contextFactory: (() => ({
        projectRepo: {
          findById: vi.fn().mockResolvedValue({ id: bootstrapInput.project_id })
        },
        sectorRepo: {
          findById: vi.fn()
        },
        locationRepo: {
          create: vi.fn()
        },
        assetRepo: {},
        topologyRepo: {},
        sectorService: {
          create: vi.fn().mockResolvedValue({ id: "sector-1" })
        },
        assetService: {
          create: vi
            .fn()
            .mockResolvedValueOnce({ id: "node-1", asset_type: "programmable_node" })
            .mockResolvedValueOnce({ id: "sensor-1", asset_type: "sensor" })
        },
        topologyService: {
          create: vi.fn().mockRejectedValue(new Error("topology create failed"))
        }
      })) as never
    });

    await expect(service.bootstrapNodeWithDevices(bootstrapInput)).rejects.toThrow("topology create failed");
    expect(transactionState).toEqual(["begin", "rollback"]);
  });
});
