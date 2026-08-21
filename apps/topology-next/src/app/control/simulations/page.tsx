import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth/auth-options";
import { buildServerContextRequest, resolveAuthenticatedControlActorFromSources } from "@/lib/auth/control-auth-session";
import { SimulationWorkbench } from "@/components/control/simulation-workbench";

export default async function ControlSimulationsPage() {
  try {
    await resolveAuthenticatedControlActorFromSources({
      session: await getServerSession(authOptions),
      request: await buildServerContextRequest("http://localhost/control/simulations")
    });
  } catch {
    redirect("/login?callbackUrl=%2Fcontrol%2Fsimulations");
  }
  return <SimulationWorkbench />;
}
