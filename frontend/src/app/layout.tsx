import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { ReactNode } from "react";
import { Providers } from "./providers";
import { SiteHeader } from "../components/site-header";

export const metadata: Metadata = {
  title: "PM Assistant",
  description:
    "AI-powered project management assistant for engineering teams.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans bg-slate-50 text-slate-900">
        <Providers>
          <SiteHeader />
          <main className="min-h-[calc(100vh-4rem)]">{children}</main>
          <footer className="border-t border-slate-200 bg-white py-6">
            <div className="mx-auto flex max-w-6xl flex-col items-center gap-2 px-6 text-sm text-slate-500 md:flex-row md:justify-between">
              <p>© {new Date().getFullYear()} PM Assistant. All rights reserved.</p>
              <div className="flex gap-4">
                <Link href="/privacy">Privacy</Link>
                <Link href="/terms">Terms</Link>
                <Link href="mailto:support@example.com">Support</Link>
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}

