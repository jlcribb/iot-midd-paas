import type { ControlActor } from "@/lib/dto/control-access.dto";

export function isAiAuthority(actor: ControlActor) {
  const identity = `${actor.actor_id ?? ""} ${actor.user_id ?? ""} ${actor.auth_provider ?? ""}`.toLowerCase();
  return (
    actor.auth_provider?.toLowerCase() === "ai" ||
    /(^|\s)ai[:_-]/.test(identity)
  );
}
