import { Children, isValidElement } from "react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { OAuthProviderButtons } from "@/components/auth/oauth-provider-buttons";

const { signInMock } = vi.hoisted(() => ({ signInMock: vi.fn() }));

vi.mock("next-auth/react", () => ({ signIn: signInMock }));

type ButtonProps = { children?: ReactNode; disabled?: boolean; onClick?: () => void };

function text(node: ReactNode): string {
  if (node == null || typeof node === "boolean") return "";
  if (typeof node === "string" || typeof node === "number") return String(node);
  return Children.toArray(node).map(text).join("");
}

function buttons(node: ReactNode, found: Array<{ label: string; props: ButtonProps }> = []) {
  if (!isValidElement(node)) return found;
  if (node.type === "button") found.push({ label: text(node.props.children), props: node.props as ButtonProps });
  Children.forEach(node.props.children, (child) => buttons(child, found));
  return found;
}

describe("OAuthProviderButtons", () => {
  it("starts Google OAuth directly with the Control Operations callback", () => {
    signInMock.mockReset();
    const tree = OAuthProviderButtons({ callbackUrl: "/control", availableProviders: ["google", "github"], labels: { google: "Continue with Google", github: "Continue with GitHub" } });
    const google = buttons(tree).find((button) => button.label === "Continue with Google");
    const github = buttons(tree).find((button) => button.label === "Continue with GitHub");

    google?.props.onClick?.();
    github?.props.onClick?.();

    expect(signInMock).toHaveBeenNthCalledWith(1, "google", { callbackUrl: "/control" });
    expect(signInMock).toHaveBeenNthCalledWith(2, "github", { callbackUrl: "/control" });
  });

  it("keeps unavailable providers visible but non-interactive", () => {
    const tree = OAuthProviderButtons({ callbackUrl: "/control", availableProviders: ["google"], labels: { google: "Continue with Google", github: "Continue with GitHub" } });
    const github = buttons(tree).find((button) => button.label === "Continue with GitHub");
    expect(github?.props.disabled).toBe(true);
    expect(github?.props.onClick).toBeUndefined();
  });
});
