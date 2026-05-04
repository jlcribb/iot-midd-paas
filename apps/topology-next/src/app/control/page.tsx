import { redirect } from "next/navigation";
import { buildServerContextRequest, resolveAuthenticatedControlActorFromSources } from "@/lib/auth/control-auth-session";
import { authOptions } from "@/lib/auth/auth-options";
import { getServerSession } from "next-auth/next";
import { ControlDashboard } from "@/components/control/control-dashboard";

export default async function ControlPage() {
  try {
    await resolveAuthenticatedControlActorFromSources({
      session: await getServerSession(authOptions),
      request: await buildServerContextRequest("http://localhost/control")
    });
  } catch {
    redirect("/login?callbackUrl=%2Fcontrol");
  }

  return <ControlDashboard />;
}
