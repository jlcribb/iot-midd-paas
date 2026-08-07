"use client";

import { signIn } from "next-auth/react";

interface OAuthLoginPanelProps {
  callbackUrl: string;
  availableProviders: string[];
  error?: string;
}

export function OAuthLoginPanel({ callbackUrl, availableProviders, error }: OAuthLoginPanelProps) {
  const hasGoogle = availableProviders.includes("google");
  const hasGitHub = availableProviders.includes("github");

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

      {error ? (
        <section className="control-alert control-alert-error">
          <strong>No se pudo completar el login.</strong>
          <span>{error}</span>
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
          <button
            className="btn btn-primary"
            disabled={!hasGoogle}
            onClick={() => void signIn("google", { callbackUrl })}
            type="button"
          >
            Entrar con Google
          </button>
          <button
            className="btn btn-secondary"
            disabled={!hasGitHub}
            onClick={() => void signIn("github", { callbackUrl })}
            type="button"
          >
            Entrar con GitHub
          </button>
        </div>
        {!hasGoogle ? <p className="control-empty">Google no está configurado en este entorno.</p> : null}
        {!hasGitHub ? <p className="control-empty">GitHub no está configurado en este entorno.</p> : null}
      </section>
    </main>
  );
}
