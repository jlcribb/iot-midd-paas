import { OAuthProviderButtons } from "@/components/auth/oauth-provider-buttons";

export const CONTROL_OAUTH_CALLBACK_URL = "/control";

/**
 * Deliberately does not authenticate or authorize. It gives an
 * unauthenticated visitor direct access to the canonical NextAuth providers.
 */
export function ControlAuthenticationRequired({ availableProviders }: { availableProviders: string[] }) {
  return (
    <main className="control-dashboard control-operations-center">
      <section className="control-header">
        <div className="control-header-main">
          <span className="control-eyebrow">Midd IOT / Governed control</span>
          <h1>Control Operations</h1>
          <p>Project-scoped operational view of policies, recommendations, simulated delivery, and attention conditions.</p>
        </div>
      </section>
      <section className="control-panel" aria-labelledby="control-authentication-required-title">
        <div className="control-panel-heading">
          <div>
            <span className="panel-kicker">Authentication required</span>
            <h2 id="control-authentication-required-title">Sign in to access Control Operations</h2>
          </div>
        </div>
        <p className="control-empty">Sign in with an authorized account to access project-scoped Control Operations.</p>
        <OAuthProviderButtons
          availableProviders={availableProviders}
          callbackUrl={CONTROL_OAUTH_CALLBACK_URL}
          labels={{ google: "Continue with Google", github: "Continue with GitHub" }}
        />
      </section>
    </main>
  );
}
