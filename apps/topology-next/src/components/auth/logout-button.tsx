"use client";

import { signOut } from "next-auth/react";

interface LogoutButtonProps {
  label?: string;
  callbackUrl?: string;
}

export function LogoutButton({ label = "Sign out", callbackUrl = "/control" }: LogoutButtonProps) {
  return (
    <button
      className="btn btn-secondary"
      onClick={() => void signOut({ callbackUrl })}
      type="button"
    >
      {label}
    </button>
  );
}
