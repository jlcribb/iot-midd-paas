import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth/auth-options";
import { OAuthLoginPanel } from "@/components/auth/oauth-login-panel";
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

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const session = await getServerSession(authOptions);
  const resolvedSearchParams = (await searchParams) ?? {};
  const callbackUrl = resolvedSearchParams.callbackUrl ?? "/control";
  const oauthStatus = getOAuthConfigurationStatus();

  if (session?.user) {
    redirect(callbackUrl);
  }

  const availableProviders = [
    oauthStatus.google.configured ? "google" : null,
    oauthStatus.github.configured ? "github" : null
  ].filter((providerId): providerId is "google" | "github" => providerId !== null);

  return (
    <OAuthLoginPanel
      availableProviders={availableProviders}
      callbackUrl={callbackUrl}
      error={loginErrorMessage(resolvedSearchParams.error)}
    />
  );
}
