"use client";

import { signOut } from "next-auth/react";

export function LogoutButton() {
  return (
    <button
      className="btn btn-secondary"
      onClick={() => void signOut({ callbackUrl: "/login" })}
      type="button"
    >
      Cerrar sesión
    </button>
  );
}
