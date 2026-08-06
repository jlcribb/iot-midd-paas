import "server-only";

export type ProviderConfigurationState = {
  configured: boolean;
  partial: boolean;
};

export type OAuthConfigurationStatus = {
  github: ProviderConfigurationState;
  google: ProviderConfigurationState;
  nextAuthSecretConfigured: boolean;
};

function normalizeCredential(value?: string) {
  return value?.trim() ?? "";
}

function isPlaceholderValue(value: string) {
  return /^replace(?:_|-|\s)with/i.test(value);
}

export function hasConfiguredCredential(value?: string) {
  const normalized = normalizeCredential(value);
  return normalized.length > 0 && !isPlaceholderValue(normalized);
}

export function getProviderConfiguration(id?: string, secret?: string): ProviderConfigurationState {
  const hasId = hasConfiguredCredential(id);
  const hasSecret = hasConfiguredCredential(secret);

  return {
    configured: hasId && hasSecret,
    partial: hasId !== hasSecret
  };
}

export function getResolvedNextAuthUrl() {
  const nextAuthUrl = normalizeCredential(process.env.NEXTAUTH_URL);
  if (nextAuthUrl) {
    return nextAuthUrl;
  }

  const legacyAuthUrl = normalizeCredential(process.env.AUTH_URL);
  return legacyAuthUrl || undefined;
}

export function getResolvedNextAuthSecret() {
  const nextAuthSecret = normalizeCredential(process.env.NEXTAUTH_SECRET);
  if (nextAuthSecret) {
    return nextAuthSecret;
  }

  const legacyAuthSecret = normalizeCredential(process.env.AUTH_SECRET);
  return legacyAuthSecret || undefined;
}

export function getOAuthConfigurationStatus(): OAuthConfigurationStatus {
  return {
    github: getProviderConfiguration(process.env.AUTH_GITHUB_ID, process.env.AUTH_GITHUB_SECRET),
    google: getProviderConfiguration(process.env.AUTH_GOOGLE_ID, process.env.AUTH_GOOGLE_SECRET),
    nextAuthSecretConfigured: hasConfiguredCredential(getResolvedNextAuthSecret())
  };
}
