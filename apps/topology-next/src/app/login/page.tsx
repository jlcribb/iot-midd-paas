import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { OAuthLoginPanel } from "@/components/auth/oauth-login-panel";
import { authOptions, getConfiguredAuthProviderIds } from "@/lib/auth/auth-options";

interface LoginPageProps {
  searchParams?: {
    callbackUrl?: string;
    error?: string;
  };
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
  const callbackUrl = searchParams?.callbackUrl ?? "/control";

  if (session?.user) {
    redirect(callbackUrl);
  }

  return (
    <OAuthLoginPanel
      availableProviders={getConfiguredAuthProviderIds()}
      callbackUrl={callbackUrl}
      error={loginErrorMessage(searchParams?.error)}
    />
  );
}
