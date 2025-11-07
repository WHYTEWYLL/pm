"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { loadSession, clearSession } from "../lib/auth";
import { useRouter, usePathname } from "next/navigation";

export function SiteHeader() {
  const [isMounted, setIsMounted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setIsMounted(true);
    const session = loadSession();
    setIsAuthenticated(!!session);

    const handleStorage = () => {
      const updated = loadSession();
      setIsAuthenticated(!!updated);
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  const handleLogout = () => {
    clearSession();
    setIsAuthenticated(false);
    router.push("/");
  };

  const linkClass = (href: string) =>
    `transition-colors hover:text-brand-700 ${
      pathname === href ? "text-brand-600" : "text-slate-600"
    }`;

  if (!isMounted) {
    return null;
  }

  return (
    <header className="border-b border-slate-200 bg-white/70 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 font-bold text-white">
            PM
          </span>
          PM Assistant
        </Link>
        <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
          <Link className={linkClass("/#features")} href="/#features">
            Features
          </Link>
          <Link className={linkClass("/#workflows")} href="/#workflows">
            Workflows
          </Link>
          <Link className={linkClass("/pricing")} href="/pricing">
            Pricing
          </Link>
          <Link className={linkClass("/docs")} href="/docs">
            Docs
          </Link>
          {isAuthenticated ? (
            <>
              <Link
                className="rounded-md border border-brand-200 bg-white px-3 py-1.5 text-brand-600 hover:border-brand-400"
                href="/dashboard"
              >
                Dashboard
              </Link>
              <button
                onClick={handleLogout}
                className="rounded-md bg-brand-600 px-3 py-1.5 text-white shadow hover:bg-brand-700"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                className="rounded-md border border-brand-200 bg-white px-3 py-1.5 text-brand-600 hover:border-brand-400"
                href="/login"
              >
                Log in
              </Link>
              <Link
                className="rounded-md bg-brand-600 px-3 py-1.5 text-white shadow hover:bg-brand-700"
                href="/register"
              >
                Sign up
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

