import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: DefaultSession["user"] & {
      id?: string;
    };
    control?: {
      actorId: string;
      role: "viewer" | "operator" | "admin";
      provider: string | null;
      providerAccountId: string | null;
      allProjects: boolean;
      projectIds: string[];
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    authProvider?: string | null;
    providerAccountId?: string | null;
    controlRole?: "viewer" | "operator" | "admin";
    allProjects?: boolean;
    projectIds?: string[];
  }
}
