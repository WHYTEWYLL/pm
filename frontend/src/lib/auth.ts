"use client";

export type AuthSession = {
  token: string;
  tenantId: string;
  email?: string;
};

const TOKEN_KEY = "pm_access_token";
const TENANT_KEY = "pm_tenant_id";
const EMAIL_KEY = "pm_user_email";

export function loadSession(): AuthSession | null {
  if (typeof window === "undefined") return null;

  const token = localStorage.getItem(TOKEN_KEY);
  const tenantId =
    localStorage.getItem(TENANT_KEY) ?? localStorage.getItem("tenant_id");
  if (!token || !tenantId) return null;

  const email = localStorage.getItem(EMAIL_KEY) || undefined;
  return { token, tenantId, email };
}

export function saveSession(session: AuthSession) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, session.token);
  localStorage.setItem(TENANT_KEY, session.tenantId);
  localStorage.setItem("tenant_id", session.tenantId);
  if (session.email) {
    localStorage.setItem(EMAIL_KEY, session.email);
  }
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TENANT_KEY);
  localStorage.removeItem("tenant_id");
  localStorage.removeItem(EMAIL_KEY);
}

