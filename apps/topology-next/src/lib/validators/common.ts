import { z } from "zod";

export const uuidSchema = z.string().uuid();
export const metadataSchema = z.record(z.unknown()).default({});

export const projectStatusSchema = z.enum(["draft", "active", "inactive", "archived"]);

export const assetTypeSchema = z.enum([
  "programmable_node",
  "sensor",
  "actuator",
  "gateway",
  "relay_module",
  "camera",
  "power_unit"
]);

export const assetStatusSchema = z.enum([
  "provisioning",
  "online",
  "offline",
  "active",
  "inactive",
  "fault",
  "maintenance",
  "retired"
]);

export const topologyRelationSchema = z.enum([
  "contains",
  "hosts",
  "reads",
  "controls",
  "connects_to",
  "routes_to",
  "depends_on",
  "powered_by",
  "mounted_on"
]);

export const topologyStatusSchema = z.enum(["planned", "active", "inactive", "fault", "retired"]);

export const topologyViewTypeSchema = z.enum(["logical", "physical", "geographic"]);
