import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth/auth-options";
import { getOAuthConfigurationStatus } from "@/lib/auth/oauth-provider-config";

interface LoginPageProps {
  searchParams?: Promise<{
    callbackUrl?: string;
    error?: string;
  }>;
}

function loginErrorMessage(error?: string) {
  if (!error) {
    return undefined;
  }

  switch (error) {
    case "OAuthSignin":
    case "OAuthCallback":
    case "OAuthCreateAccount":
      return "Falló el flujo OAuth con el provider seleccionado.";
    case "AccessDenied":
      return "El acceso fue denegado por la configuración de autenticación.";
    default:
      return "No se pudo completar la autenticación.";
  }
}

function buildProviderSignInHref(providerId: "github" | "google", callbackUrl: string) {
  return `/api/auth/signin/${providerId}?callbackUrl=${encodeURIComponent(callbackUrl)}`;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const session = await getServerSession(authOptions);
  const resolvedSearchParams = (await searchParams) ?? {};
  const callbackUrl = resolvedSearchParams.callbackUrl ?? "/control";
  const oauthStatus = getOAuthConfigurationStatus();

  if (session?.user) {
    redirect(callbackUrl);
  }

  return (
    <main className="control-dashboard">
      <section className="control-header">
        <div className="control-header-main">
          <span className="control-eyebrow">Midd IOT / OAuth Session</span>
          <h1>Acceso a control operativo</h1>
          <p>
            Iniciá sesión para acceder a dashboard, observabilidad y gestión de policies. La autenticación define quién
            sos; el RBAC operacional decide qué podés hacer.
          </p>
        </div>
      </section>

      {resolvedSearchParams.error ? (
        <section className="control-alert control-alert-error">
          <strong>No se pudo completar el login.</strong>
          <span>{loginErrorMessage(resolvedSearchParams.error)}</span>
        </section>
      ) : null}

      <section className="control-panel">
        <div className="control-panel-heading">
          <div>
            <span className="panel-kicker">OAuth</span>
            <h2>Elegí un provider</h2>
          </div>
        </div>
        <div className="control-actions">
          {oauthStatus.google.configured ? (
            <a className="btn btn-primary" href={buildProviderSignInHref("google", callbackUrl)}>
              Entrar con Google
            </a>
          ) : (
            <button className="btn btn-primary" disabled type="button">
              Entrar con Google
            </button>
          )}
          {oauthStatus.github.configured ? (
            <a className="btn btn-secondary" href={buildProviderSignInHref("github", callbackUrl)}>
              Entrar con GitHub
            </a>
          ) : (
            <button className="btn btn-secondary" disabled type="button">
              Entrar con GitHub
            </button>
          )}
        </div>
        {!oauthStatus.google.configured ? (
          <p className="control-empty">Google no está configurado en este entorno.</p>
        ) : null}
        {!oauthStatus.github.configured ? (
          <p className="control-empty">GitHub no está configurado en este entorno.</p>
        ) : null}
      </section>
    </main>
  );
}
