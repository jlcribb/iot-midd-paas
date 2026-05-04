import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth/auth-options";
import { buildServerContextRequest, resolveAuthenticatedControlActorFromSources } from "@/lib/auth/control-auth-session";
import { ControlPolicyManagement } from "@/components/control/control-policy-management";

export default async function ControlPoliciesPage() {
  try {
    await resolveAuthenticatedControlActorFromSources({
      session: await getServerSession(authOptions),
      request: await buildServerContextRequest("http://localhost/control/policies")
    });
  } catch {
    redirect("/login?callbackUrl=%2Fcontrol%2Fpolicies");
  }

  return <ControlPolicyManagement />;
}
