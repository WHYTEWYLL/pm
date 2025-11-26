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
    <header className="bg-white">
      <div className="mx-auto flex w-full max-w-6xl items-center px-6 py-5 relative">
        {/* Left side: Logo */}
        <div className="flex items-center">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-slate-900">
            <span className="relative inline-flex h-7 w-7 items-center justify-center">
              <span className="absolute inset-0 rounded-full bg-blue-600"></span>
              <span className="absolute left-1.5 top-1/2 h-4 w-4 -translate-y-1/2 rounded-full bg-white"></span>
            </span>
            Corta.ai
          </Link>
        </div>

        {/* Center: Toggle - Context-aware */}
        {pathname === "/" && (
          <div className="absolute left-1/2 -translate-x-1/2 flex items-center rounded-full bg-slate-100 p-1">
            <button
              onClick={() => handleAudienceToggle("devs")}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition-all duration-200 ${
                audience === "devs"
                  ? "bg-blue-600 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Build
            </button>
            <Link
              href="/#stakeholders-section"
              onClick={(e) => {
                e.preventDefault();
                handleAudienceToggle("stakeholders");
              }}
              className="flex items-center"
            >
              <div className="mx-2 h-4 w-px bg-slate-300"></div>
            </Link>
            <button
              onClick={() => handleAudienceToggle("stakeholders")}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition-all duration-200 ${
                audience === "stakeholders"
                  ? "bg-slate-900 text-white shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Make decisions
            </button>
          </div>
        )}


        {/* Right side: Nav + Auth */}
        <div className="flex items-center gap-6 text-sm font-medium text-slate-600 ml-auto">
          {/* Hide Pricing and Dashboard links when on dashboard */}
          {!pathname?.startsWith("/dashboard") && (
            <>
              <Link className="hover:text-slate-900 transition-colors" href="/pricing">
                Pricing
              </Link>
              {isAuthenticated && (
                <Link
                  className="hover:text-slate-900 transition-colors"
                  href="/dashboard"
                >
                  Dashboard
                </Link>
              )}
            </>
          )}
          {isAuthenticated ? (
            <button
              onClick={handleLogout}
              className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
            >
              Log out
            </button>
          ) : (
            <>
              <Link
                className="hover:text-slate-900 transition-colors"
                href="/login"
              >
                Sign in
              </Link>
              <Link
                className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
                href="/register"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

