import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";
import { LogoutButton } from "@/components/auth/logout-button";

const { signOutMock } = vi.hoisted(() => ({ signOutMock: vi.fn() }));

vi.mock("next-auth/react", () => ({ signOut: signOutMock }));

type LogoutButtonElement = ReactElement<{ children: string; onClick: () => void }>;

describe("LogoutButton", () => {
  it("uses canonical NextAuth signOut and returns to Control Operations", () => {
    signOutMock.mockReset();
    const button = LogoutButton({}) as LogoutButtonElement;

    button.props.onClick();

    expect(button.props.children).toBe("Sign out");
    expect(signOutMock).toHaveBeenCalledWith({ callbackUrl: "/control" });
  });

  it("uses the same canonical session exit for account switching", () => {
    signOutMock.mockReset();
    const button = LogoutButton({ label: "Change account" }) as LogoutButtonElement;

    button.props.onClick();

    expect(button.props.children).toBe("Change account");
    expect(signOutMock).toHaveBeenCalledWith({ callbackUrl: "/control" });
  });
});
