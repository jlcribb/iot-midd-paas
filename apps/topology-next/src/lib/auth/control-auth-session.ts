import type { Session } from "next-auth";
import { getServerSession } from "next-auth/next";
import { headers } from "next/headers";
import type { ControlActor, ControlRole } from "@/lib/dto/control-access.dto";
import { authOptions } from "@/lib/auth/auth-options";
import { resolveControlActor, resolveRoleFromEmail } from "@/lib/auth/control-access";
import { UnauthorizedError } from "@/lib/errors/domain-errors";

function parseBooleanFlag(value: string | undefined) {
  return value?.trim().toLowerCase() === "true";
}

function normalizeEmail(email: string | null | undefined) {
  return email?.trim().toLowerCase() ?? null;
}

function normalizeUsername(session: Session) {
  return session.user?.email ?? session.user?.name ?? null;
}

function buildActorId(input: { email: string | null; provider: string | null; providerAccountId: string | null }) {
  if (input.email) {
    return input.email;
  }
  if (input.provider && input.providerAccountId) {
    return `${input.provider}:${input.providerAccountId}`;
  }
  if (input.providerAccountId) {
    return input.providerAccountId;
  }
  return "authenticated-control-user";
}

export function isDevFallbackEnabled() {
  return process.env.NODE_ENV !== "production" && parseBooleanFlag(process.env.CONTROL_RBAC_ALLOW_DEV_FALLBACK);
}

export function buildAuthenticatedControlActorFromSession(session: Session): ControlActor {
  const email = normalizeEmail(session.user?.email);
  const provider = session.control?.provider ?? null;
  const providerAccountId = session.control?.providerAccountId ?? null;
  const actorId = buildActorId({
    email,
    provider,
    providerAccountId
  });

  return {
    actor_id: actorId,
    user_id: actorId,
    username: normalizeUsername(session),
    display_name: session.user?.name ?? session.user?.email ?? null,
    email,
    image: session.user?.image ?? null,
    auth_provider: provider,
    provider_account_id: providerAccountId,
    auth_source: "oauth_session",
    role: session.control?.role ?? resolveRoleFromEmail(email),
    all_projects: session.control?.allProjects ?? true,
    project_ids: session.control?.projectIds ?? []
  };
}

export async function resolveAuthenticatedControlActorFromSources(args: {
  session: Session | null;
  request?: Request;
}): Promise<ControlActor> {
  if (args.session?.user) {
    return buildAuthenticatedControlActorFromSession(args.session);
  }

  if (args.request && isDevFallbackEnabled()) {
    const fallbackActor = resolveControlActor(args.request);
    return {
      ...fallbackActor,
      actor_id: fallbackActor.user_id,
      username: fallbackActor.user_id,
      email: null,
      image: null,
      auth_provider: null,
      provider_account_id: null,
      auth_source: "dev_fallback"
    };
  }

  throw new UnauthorizedError("Authentication required for control operations");
}

export async function resolveAuthenticatedControlActor(request?: Request): Promise<ControlActor> {
  const session = await getServerSession(authOptions);
  return resolveAuthenticatedControlActorFromSources({
    session,
    request
  });
}

export async function buildServerContextRequest(url = "http://localhost/") {
  const currentHeaders = await headers();
  return new Request(url, {
    headers: new Headers(currentHeaders)
  });
}
