"use client";

import { signIn } from "next-auth/react";

export type OAuthProviderId = "google" | "github";

interface OAuthProviderButtonsProps {
  callbackUrl: string;
  availableProviders: string[];
  labels?: Partial<Record<OAuthProviderId, string>>;
}

const defaultLabels: Record<OAuthProviderId, string> = {
  google: "Entrar con Google",
  github: "Entrar con GitHub"
};

export function OAuthProviderButtons({ callbackUrl, availableProviders, labels = {} }: OAuthProviderButtonsProps) {
  const startSignIn = (provider: OAuthProviderId) => {
    void signIn(provider, { callbackUrl });
  };

  return (
    <div className="control-actions">
      {(["google", "github"] as const).map((provider) => {
        const enabled = availableProviders.includes(provider);
        return (
          <button
            className={provider === "google" ? "btn btn-primary" : "btn btn-secondary"}
            disabled={!enabled}
            key={provider}
            onClick={enabled ? () => startSignIn(provider) : undefined}
            type="button"
          >
            {labels[provider] ?? defaultLabels[provider]}
          </button>
        );
      })}
    </div>
  );
}
