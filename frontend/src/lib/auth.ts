"use client";

import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type AuthSession = {
  token: string;
  tenantId: string;
  email?: string;
};

export type UserInfo = {
  id: string;
  email: string;
  full_name?: string;
  email_verified: boolean;
  tenant_id?: string;
  default_view: "dev" | "stakeholder";
  permission: "admin" | "member";
  onboarding_completed: boolean;
  is_owner: boolean;
};

const TOKEN_KEY = "pm_access_token";
const TENANT_KEY = "pm_tenant_id";
const EMAIL_KEY = "pm_user_email";
const VIEW_KEY = "pm_user_view";

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
  localStorage.removeItem(VIEW_KEY);
}

export function getCurrentView(): "dev" | "stakeholder" {
  if (typeof window === "undefined") return "dev";
  return (localStorage.getItem(VIEW_KEY) as "dev" | "stakeholder") || "dev";
}

export function setCurrentView(view: "dev" | "stakeholder") {
  if (typeof window === "undefined") return;
  localStorage.setItem(VIEW_KEY, view);
}

export async function fetchUserInfo(): Promise<UserInfo | null> {
  const session = loadSession();
  if (!session) return null;

  try {
    const response = await axios.get(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${session.token}` },
    });
    return response.data;
  } catch {
    return null;
  }
}

export async function completeOnboarding(
  defaultView: "dev" | "stakeholder"
): Promise<boolean> {
  const session = loadSession();
  if (!session) return false;

  try {
    await axios.post(
      `${API_URL}/api/auth/me/onboarding`,
      { default_view: defaultView, onboarding_completed: true },
      { headers: { Authorization: `Bearer ${session.token}` } }
    );
    setCurrentView(defaultView);
    return true;
  } catch {
    return false;
  }
}

export async function updateUserView(
  view: "dev" | "stakeholder"
): Promise<boolean> {
  const session = loadSession();
  if (!session) return false;

  try {
    await axios.put(
      `${API_URL}/api/auth/me/view`,
      { default_view: view },
      { headers: { Authorization: `Bearer ${session.token}` } }
    );
    setCurrentView(view);
    return true;
  } catch {
    return false;
  }
}
