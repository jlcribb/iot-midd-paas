import { Children, isValidElement } from "react";
import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { OAuthLoginPanel } from "@/components/auth/oauth-login-panel";

const { signInMock } = vi.hoisted(() => ({
  signInMock: vi.fn()
}));

vi.mock("next-auth/react", () => ({
  signIn: signInMock
}));

type ButtonProps = {
  children?: ReactNode;
  disabled?: boolean;
  onClick?: () => void;
};

function flattenText(node: ReactNode): string {
  if (node == null || typeof node === "boolean") {
    return "";
  }

  if (typeof node === "string" || typeof node === "number") {
    return String(node);
  }

  return Children.toArray(node)
    .map((child) => flattenText(child))
    .join("");
}

function collectButtons(node: ReactNode, buttons: Array<{ label: string; props: ButtonProps }> = []) {
  if (!isValidElement(node)) {
    return buttons;
  }

  if (typeof node.type === "string" && node.type === "button") {
    buttons.push({
      label: flattenText(node.props.children),
      props: node.props as ButtonProps
    });
  }

  Children.forEach(node.props.children, (child) => {
    collectButtons(child, buttons);
  });

  return buttons;
}

describe("OAuthLoginPanel", () => {
  it("invokes signIn with callbackUrl for enabled providers", () => {
    signInMock.mockReset();

    const tree = OAuthLoginPanel({
      callbackUrl: "/control",
      availableProviders: ["google", "github"]
    });
    const buttons = collectButtons(tree);
    const githubButton = buttons.find((button) => button.label === "Entrar con GitHub");
    const googleButton = buttons.find((button) => button.label === "Entrar con Google");

    expect(githubButton?.props.disabled).toBe(false);
    expect(googleButton?.props.disabled).toBe(false);

    githubButton?.props.onClick?.();
    googleButton?.props.onClick?.();

    expect(signInMock).toHaveBeenNthCalledWith(1, "github", { callbackUrl: "/control" });
    expect(signInMock).toHaveBeenNthCalledWith(2, "google", { callbackUrl: "/control" });
  });

  it("renders provider-specific messages when a provider is unavailable", () => {
    const html = renderToStaticMarkup(
      OAuthLoginPanel({
        callbackUrl: "/control",
        availableProviders: ["github"]
      })
    );

    expect(html).toContain("Entrar con Google");
    expect(html).toContain("Entrar con GitHub");
    expect(html).toContain("Google no est");
    expect(html).not.toContain("GitHub no est");
  });
});
