import type { NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";
import GoogleProvider from "next-auth/providers/google";
import { resolvePersistedProjectControlAccess } from "@/lib/services/project-control-membership.service";
import {
  getOAuthConfigurationStatus,
  getResolvedNextAuthSecret,
  getResolvedNextAuthUrl
} from "@/lib/auth/oauth-provider-config";

const resolvedNextAuthUrl = getResolvedNextAuthUrl();
if (!process.env.NEXTAUTH_URL && resolvedNextAuthUrl) {
  process.env.NEXTAUTH_URL = resolvedNextAuthUrl;
}

function buildProviders() {
  const providers: NextAuthOptions["providers"] = [];
  const oauthStatus = getOAuthConfigurationStatus();
  const googleClientId = process.env.AUTH_GOOGLE_ID?.trim();
  const googleClientSecret = process.env.AUTH_GOOGLE_SECRET?.trim();
  const githubClientId = process.env.AUTH_GITHUB_ID?.trim();
  const githubClientSecret = process.env.AUTH_GITHUB_SECRET?.trim();

  if (oauthStatus.google.configured && googleClientId && googleClientSecret) {
    providers.push(
      GoogleProvider({
        clientId: googleClientId,
        clientSecret: googleClientSecret
      })
    );
  }

  if (oauthStatus.github.configured && githubClientId && githubClientSecret) {
    providers.push(
      GitHubProvider({
        clientId: githubClientId,
        clientSecret: githubClientSecret
      })
    );
  }

  return providers;
}

export const authOptions: NextAuthOptions = {
  secret: getResolvedNextAuthSecret(),
  session: {
    strategy: "jwt"
  },
  pages: {
    signIn: "/login"
  },
  providers: buildProviders(),
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.authProvider = account.provider ?? null;
        token.providerAccountId = account.providerAccountId ?? null;
      }

      const access = await resolvePersistedProjectControlAccess(token.email ?? null);
      token.controlRole = access.role;
      token.allProjects = access.allProjects;
      token.projectIds = access.projectIds;
      token.projectRoles = access.projectRoles;

      return token;
    },
    async session({ session, token }) {
      if (!session.user) {
        session.user = {};
      }

      session.user.id = token.sub ?? token.email ?? "authenticated-control-user";
      session.control = {
        actorId: token.sub ?? token.email ?? "authenticated-control-user",
        role: token.controlRole ?? "viewer",
        provider: token.authProvider ?? null,
        providerAccountId: token.providerAccountId ?? null,
        allProjects: token.allProjects ?? false,
        projectIds: token.projectIds ?? [],
        projectRoles: token.projectRoles ?? {}
      };

      return session;
    }
  }
};

export function getConfiguredAuthProviderIds() {
  return buildProviders().map((provider) => provider.id);
}
