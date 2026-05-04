import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth/auth-options";
import { LogoutButton } from "@/components/auth/logout-button";

export default async function LogoutPage() {
  const session = await getServerSession(authOptions);

  if (!session?.user) {
    redirect("/login");
  }

  return (
    <main className="control-dashboard">
      <section className="control-panel">
        <div className="control-panel-heading">
          <div>
            <span className="panel-kicker">Session</span>
            <h2>Cerrar sesión</h2>
          </div>
        </div>
        <p className="control-empty">La sesión actual pertenece a {session.user?.email ?? session.user?.name ?? "usuario autenticado"}.</p>
        <div className="control-actions">
          <LogoutButton />
        </div>
      </section>
    </main>
  );
}
