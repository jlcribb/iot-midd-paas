import type { NextAuthOptions } from "next-auth";
import GitHubProvider from "next-auth/providers/github";
import GoogleProvider from "next-auth/providers/google";
import { resolveRoleFromEmail } from "@/lib/auth/control-access";

if (!process.env.NEXTAUTH_URL && process.env.AUTH_URL) {
  process.env.NEXTAUTH_URL = process.env.AUTH_URL;
}

function buildProviders() {
  const providers = [];

  if (process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET) {
    providers.push(
      GoogleProvider({
        clientId: process.env.AUTH_GOOGLE_ID,
        clientSecret: process.env.AUTH_GOOGLE_SECRET
      })
    );
  }

  if (process.env.AUTH_GITHUB_ID && process.env.AUTH_GITHUB_SECRET) {
    providers.push(
      GitHubProvider({
        clientId: process.env.AUTH_GITHUB_ID,
        clientSecret: process.env.AUTH_GITHUB_SECRET
      })
    );
  }

  return providers;
}

export const authOptions: NextAuthOptions = {
  secret: process.env.AUTH_SECRET ?? process.env.NEXTAUTH_SECRET,
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

      token.controlRole = resolveRoleFromEmail(token.email ?? null);
      token.allProjects = true;
      token.projectIds = [];

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
        allProjects: token.allProjects ?? true,
        projectIds: token.projectIds ?? []
      };

      return session;
    }
  }
};

export function getConfiguredAuthProviderIds() {
  return authOptions.providers.map((provider) => provider.id);
}
