"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { loadSession, clearSession } from "../lib/auth";
import { useRouter, usePathname } from "next/navigation";

type AudienceType = "devs" | "stakeholders";

export function SiteHeader() {
  const [isMounted, setIsMounted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [audience, setAudience] = useState<AudienceType>("devs");
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

  const handleAudienceToggle = (newAudience: AudienceType) => {
    setAudience(newAudience);
    const sectionId = newAudience === "devs" ? "devs-section" : "stakeholders-section";
    
    if (pathname === "/") {
      // Scroll to the appropriate section
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 50);
    } else {
      // If not on home page, navigate to home with hash
      router.push(`/#${sectionId}`);
    }
  };

  // Sync with URL hash on mount
  useEffect(() => {
    if (pathname === "/") {
      const hash = window.location.hash;
      if (hash === "#stakeholders-section") {
        setAudience("stakeholders");
      } else if (hash === "#devs-section") {
        setAudience("devs");
      }
    }
  }, [pathname]);

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
          <span className="relative inline-flex h-8 w-8 items-center justify-center">
            {/* Blue circle - base layer */}
            <span className="absolute inset-0 rounded-full bg-blue-600"></span>
            {/* White circle on top - offset to the right to create crescent moon effect on the left */}
            <span className="absolute left-2 top-1/2 h-5 w-5 -translate-y-1/2 rounded-full bg-white"></span>
          </span>
          Corta.ai
        </Link>
        <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
          {/* Audience Toggle - only show on home page */}
          {pathname === "/" && (
            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white p-1">
              <button
                onClick={() => handleAudienceToggle("devs")}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                  audience === "devs"
                    ? "bg-brand-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                Devs
              </button>
              <button
                onClick={() => handleAudienceToggle("stakeholders")}
                className={`rounded-md px-3 py-1.5 text-xs font-semibold transition ${
                  audience === "stakeholders"
                    ? "bg-brand-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                Stakeholders
              </button>
            </div>
          )}
          <Link className={linkClass("/#features")} href="/#features">
            Features
          </Link>
          <Link className={linkClass("/#workflows")} href="/#workflows">
            Workflows
          </Link>
          <Link className={linkClass("/pricing")} href="/pricing">
            Pricing
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

