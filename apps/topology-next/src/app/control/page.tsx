import { buildServerContextRequest, resolveAuthenticatedControlActorFromSources } from "@/lib/auth/control-auth-session";
import { authOptions } from "@/lib/auth/auth-options";
import { getServerSession } from "next-auth/next";
import { ControlDashboard } from "@/components/control/control-dashboard";
import { ControlAuthenticationRequired } from "@/components/control/control-authentication-required";
import { getOAuthConfigurationStatus } from "@/lib/auth/oauth-provider-config";

function configuredOAuthProviders() {
  const status = getOAuthConfigurationStatus();
  return [
    status.google.configured ? "google" : null,
    status.github.configured ? "github" : null
  ].filter((provider): provider is "google" | "github" => provider !== null);
}

export default async function ControlPage() {
  const session = await getServerSession(authOptions);
  try {
    await resolveAuthenticatedControlActorFromSources({
      session,
      request: await buildServerContextRequest("http://localhost/control")
    });
  } catch {
    if (!session?.user) {
      return <ControlAuthenticationRequired availableProviders={configuredOAuthProviders()} />;
    }
    throw new Error("Authenticated control actor could not be resolved");
  }

  return <ControlDashboard />;
}
