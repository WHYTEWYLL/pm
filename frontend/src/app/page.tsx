"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function LandingPage() {
  const [audience, setAudience] = useState<"devs" | "stakeholders">("devs");

  useEffect(() => {
    // Check URL hash for audience preference
    const hash = window.location.hash;
    if (hash === "#stakeholders-section") {
      setAudience("stakeholders");
      setTimeout(() => {
        const element = document.getElementById("stakeholders-section");
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    } else if (hash === "#devs-section") {
      setAudience("devs");
      setTimeout(() => {
        const element = document.getElementById("devs-section");
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    }

    // Listen for hash changes
    const handleHashChange = () => {
      const newHash = window.location.hash;
      if (newHash === "#stakeholders-section") {
        setAudience("stakeholders");
      } else if (newHash === "#devs-section") {
        setAudience("devs");
      }
    };

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  return (
    <div className="relative overflow-hidden bg-white">
      {/* Hero Section - Minimal with lots of whitespace */}
      <section className="relative min-h-[85vh] flex items-center">
        <div className="absolute inset-0 -z-10">
          {/* Abstract geometric background */}
          <div className="absolute top-20 right-20 w-96 h-96 bg-blue-50 rounded-full blur-3xl opacity-30"></div>
          <div className="absolute bottom-20 left-20 w-96 h-96 bg-slate-50 rounded-full blur-3xl opacity-30"></div>
        </div>
        <div className="mx-auto max-w-4xl px-6 py-32 lg:py-40">
          <div className="text-center">
            <h1 className="text-6xl font-light tracking-tight text-slate-900 sm:text-7xl lg:text-8xl mb-8">
              Developers
            </h1>
            <p className="mt-8 text-2xl font-light text-slate-600 sm:text-3xl lg:text-4xl mb-8 max-w-3xl mx-auto leading-relaxed">
              Let your work speak for itself. Don't get gotcha by politics, status updates, or explaining what you're working on. 
            </p>
            <p className="mt-6 text-lg text-slate-500 sm:text-xl max-w-2xl mx-auto leading-relaxed">
              I'll watch your Slack, Linear, and GitHub activity and automatically sync everything. I'll track progress, clean up tickets, and unblock your team—so you can focus on building. I'll help 🔥
            </p>
            <div className="mt-16 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-4">
              <a
                href="#devs-section"
                onClick={(e) => {
                  e.preventDefault();
                  setAudience("devs");
                  document.getElementById("devs-section")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="w-full sm:w-auto px-10 py-3.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors duration-200 rounded-sm"
              >
                Build
              </a>
              <a
                href="#stakeholders-section"
                onClick={(e) => {
                  e.preventDefault();
                  setAudience("stakeholders");
                  document.getElementById("stakeholders-section")?.scrollIntoView({ behavior: "smooth" });
                }}
                className="w-full sm:w-auto px-10 py-3.5 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 transition-colors duration-200 rounded-sm"
              >
                Make decisions
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Key Message Banner - Minimal */}
      <section className="border-t border-b border-slate-200 bg-white py-12">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="text-base font-light text-slate-700 sm:text-lg leading-relaxed">
            <span className="font-normal">Corta is not a chatbot.</span> Cut the noise between you and your team.
          </p>
          <p className="mt-4 text-base text-slate-500 sm:text-lg font-light">
            Corta is the operating system of product execution.
          </p>
          <p className="mt-3 text-sm text-slate-400 font-light">
            It works continuously, automatically, and without prompting.
          </p>
        </div>
      </section>

      {/* Devs Section - Clean and minimal */}
      <section id="devs-section" className="bg-white py-32 scroll-mt-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-20 text-center">
            <h2 className="text-4xl font-light text-slate-900 sm:text-5xl mb-6">
              For Development Teams
            </h2>
            <p className="mt-6 text-lg text-slate-500 font-light max-w-2xl mx-auto leading-relaxed">
              Keep everyone aligned. Track progress. Clean up tickets. Ensure no one is blocked.
            </p>
          </div>

          <div className="grid gap-12 lg:grid-cols-3 lg:gap-8">
            {[
              {
                title: "Tracks Progress",
                description:
                  "Automatically syncs Slack conversations, GitHub PRs, and Linear tickets to give you real-time visibility into what's happening.",
              },
              {
                title: "Cleans Up Tickets",
                description:
                  "AI-powered ticket hygiene that moves stale issues, closes duplicates, and keeps your backlog organized without manual work.",
              },
              {
                title: "Prevents Blockers",
                description:
                  "Detects blockers in conversations and automatically creates or updates tickets to keep your team moving forward.",
              },
            ].map((feature, idx) => (
              <div
                key={idx}
                className="group"
              >
                <div className="h-px w-12 bg-blue-600 mb-6"></div>
                <h3 className="text-xl font-normal text-slate-900 mb-4">{feature.title}</h3>
                <p className="text-sm text-slate-500 font-light leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-20 text-center">
            <Link
              href="/register"
              className="inline-block px-10 py-3.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors duration-200 rounded-sm"
            >
              Get Started for Teams
            </Link>
          </div>
        </div>
      </section>

      {/* Stakeholders Section - Clean and minimal */}
      <section id="stakeholders-section" className="bg-slate-50 py-32 scroll-mt-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-20 text-center">
            <h2 className="text-4xl font-light text-slate-900 sm:text-5xl mb-6">
              For Stakeholders
            </h2>
            <p className="mt-6 text-lg text-slate-500 font-light max-w-2xl mx-auto leading-relaxed">
              Weekly updates. Executive summaries. Context-rich progress reports. Audience-aware communication.
            </p>
          </div>

          <div className="grid gap-12 lg:grid-cols-3 lg:gap-8">
            {[
              {
                title: "Weekly Updates",
                description:
                  "Automatically generated Friday summaries of what shipped, what's in progress, and what's blocked—no PM overhead required.",
              },
              {
                title: "Executive Summaries",
                description:
                  "High-level progress reports tailored for leadership, highlighting key accomplishments and strategic insights.",
              },
              {
                title: "Context-Rich Reports",
                description:
                  "Progress reports that include the full context—not just status updates, but the why and how behind each milestone.",
              },
            ].map((feature, idx) => (
              <div
                key={idx}
                className="group"
              >
                <div className="h-px w-12 bg-slate-400 mb-6"></div>
                <h3 className="text-xl font-normal text-slate-900 mb-4">{feature.title}</h3>
                <p className="text-sm text-slate-500 font-light leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-20 text-center">
            <Link
              href="/register"
              className="inline-block px-10 py-3.5 text-sm font-medium text-slate-700 border border-slate-300 hover:border-slate-400 hover:bg-white transition-colors duration-200 rounded-sm bg-white"
            >
              Get Started for Stakeholders
            </Link>
          </div>
        </div>
      </section>

      {/* How Corta Works - Minimal */}
      <section className="bg-white py-32">
        <div className="mx-auto max-w-4xl px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-light text-slate-900 sm:text-5xl mb-4">
              How Corta Works
            </h2>
            <p className="mt-6 text-base font-light text-blue-600 uppercase tracking-wider text-xs">
              The Magic
            </p>
            <p className="mt-8 text-lg text-slate-500 font-light sm:text-xl max-w-2xl mx-auto leading-relaxed">
              It observes. It organizes. It communicates. Automatically.
            </p>
            <p className="mt-6 text-base text-slate-600 font-normal">
              No prompts. No micromanagement.
            </p>
          </div>

          <div className="border-t border-b border-slate-200 py-16">
            <div className="space-y-8 text-center">
              <p className="text-base text-slate-600 font-light leading-relaxed">
                Corta plugs into the tools your team already uses
              </p>
              <p className="text-base text-slate-600 font-light leading-relaxed">
                and behaves like the PM that never forgets anything.
              </p>
              <p className="text-lg font-normal text-slate-900 mt-8">
                Let everyone's work speak for itself.
              </p>
            </div>

            {/* Integration Icons - Minimal */}
            <div className="mt-16 flex flex-wrap items-center justify-center gap-12">
              {["Slack", "Linear", "GitHub"].map((tool) => (
                <div
                  key={tool}
                  className="flex flex-col items-center gap-4 group"
                >
                  <div className="h-16 w-16 rounded-full bg-blue-50 border border-blue-100 flex items-center justify-center transition-all duration-200 group-hover:bg-blue-100">
                    <div className="h-8 w-8 rounded bg-blue-600 opacity-20"></div>
                  </div>
                  <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{tool}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials - Minimal */}
      <section className="bg-slate-50 py-32">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="mb-16 text-center text-3xl font-light text-slate-900">
            What Teams Are Saying
          </h2>
          <div className="grid gap-12 md:grid-cols-3">
            {[
              {
                quote: "Corta removed 60% of my PM overhead.",
                author: "Project Manager",
              },
              {
                quote:
                  "It keeps leadership synced without me writing a single update.",
                author: "Engineering Lead",
              },
              {
                quote:
                  "Our engineers finally stay in sync without me manually pinging them.",
                author: "Tech Lead",
              },
            ].map((testimonial, idx) => (
              <div
                key={idx}
                className="border-t border-slate-200 pt-8"
              >
                <p className="text-base text-slate-700 font-light leading-relaxed mb-6">
                  "{testimonial.quote}"
                </p>
                <p className="text-xs text-slate-400 font-light uppercase tracking-wider">— {testimonial.author}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action - Minimal */}
      <section className="bg-blue-600 py-32">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-4xl font-light text-white sm:text-5xl mb-6">
            Get early access
          </h2>
          <p className="mt-6 text-lg text-blue-100 font-light">
            Corta handles the work behind the work.
          </p>
          <div className="mt-12">
            <Link
              href="/register"
              className="inline-block px-10 py-3.5 text-sm font-medium text-blue-600 bg-white hover:bg-slate-50 transition-colors duration-200 rounded-sm"
            >
              Start Free Trial
            </Link>
          </div>
          <p className="mt-8 text-sm text-blue-200 font-light">
            No credit card required • 7-day free trial
          </p>
        </div>
      </section>

      {/* Footer Message - Minimal */}
      <section className="border-t border-slate-200 bg-white py-12">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <p className="text-sm text-slate-400 font-light">
            <span className="font-normal text-slate-600">Corta is not a chatbot.</span>{" "}
            Cut the noise between you and your team.
          </p>
          <p className="mt-3 text-sm text-slate-400 font-light">
            Corta is the operating system of product execution.
          </p>
        </div>
      </section>
    </div>
  );
}
