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
      {/* Hero Section - Corta Introduction */}
      <section className="relative min-h-[85vh] flex items-center">
        <div className="absolute inset-0 -z-10">
          {/* Abstract geometric background */}
          <div className="absolute top-20 right-20 w-96 h-96 bg-blue-50 rounded-full blur-3xl opacity-30"></div>
          <div className="absolute bottom-20 left-20 w-96 h-96 bg-slate-50 rounded-full blur-3xl opacity-30"></div>
        </div>
        <div className="mx-auto max-w-4xl px-6 py-32 lg:py-40">
          <div className="text-center">
            <h1 className="text-6xl font-light tracking-tight text-slate-900 sm:text-7xl lg:text-8xl mb-8">
              Hi, I'm Corta.
            </h1>
            <p className="mt-8 text-2xl font-light text-slate-600 sm:text-3xl mb-6 max-w-2xl mx-auto leading-relaxed">
              I track your team's work so nothing falls through the cracks.
            </p>
            <p className="text-lg text-slate-500 max-w-xl mx-auto">
              Conversations. Decisions. Blockers. All synced automatically.
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
                Meet Corta for Teams
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
                Meet Corta for Stakeholders
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Devs Section */}
      <section id="devs-section" className="bg-slate-50 py-24 scroll-mt-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-light text-slate-900 sm:text-5xl mb-6">
              Developers
            </h2>
            <p className="text-xl text-slate-600 font-light max-w-xl mx-auto">
              Let your work speak for itself. I handle the rest.
            </p>
          </div>

          <div className="grid gap-10 lg:grid-cols-3">
            {[
              {
                title: "Tracks Progress",
                description: "I sync Slack, GitHub, and Linear automatically.",
              },
              {
                title: "Cleans Tickets",
                description: "I close duplicates and move stale issues.",
              },
              {
                title: "Prevents Blockers",
                description: "I spot blockers and flag them before they slow you down.",
              },
            ].map((feature, idx) => (
              <div key={idx}>
                <div className="h-px w-12 bg-blue-600 mb-4"></div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-500">{feature.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Link
              href="/register"
              className="inline-block px-8 py-3 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors rounded-sm"
            >
              Get Started
            </Link>
          </div>
        </div>
      </section>

      {/* Leadership Section */}
      <section id="stakeholders-section" className="bg-white py-24 scroll-mt-20">
        <div className="mx-auto max-w-5xl px-6">
          <div className="mb-16 text-center">
            <h2 className="text-4xl font-light text-slate-900 sm:text-5xl mb-6">
              Leadership
            </h2>
            <p className="text-xl text-slate-600 font-light max-w-xl mx-auto">
              Know what's happening. Without chasing anyone.
            </p>
          </div>

          <div className="grid gap-10 lg:grid-cols-3">
            {[
              {
                title: "Weekly Updates",
                description: "Every Friday you get a summary. What shipped. What's blocked.",
              },
              {
                title: "Executive Summaries",
                description: "Progress reports written for leadership. No jargon.",
              },
              {
                title: "Full Context",
                description: "Not just status. The why behind every milestone.",
              },
            ].map((feature, idx) => (
              <div key={idx}>
                <div className="h-px w-12 bg-slate-400 mb-4"></div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-500">{feature.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Link
              href="/register"
              className="inline-block px-8 py-3 text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 transition-colors rounded-sm"
            >
              Get Started
            </Link>
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className="bg-slate-50 py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-3xl font-light text-slate-900 mb-4">
            Works with your tools
          </h2>
          <p className="text-base text-slate-500 mb-12">
            I plug into what you already use.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-12">
            {/* Slack */}
            <div className="flex flex-col items-center gap-3 group">
              <div className="h-14 w-14 rounded-full bg-white border border-slate-200 flex items-center justify-center transition-all group-hover:border-slate-300 group-hover:shadow-sm">
                <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none">
                  <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" fill="#E01E5A"/>
                </svg>
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Slack</span>
            </div>
            {/* Linear */}
            <div className="flex flex-col items-center gap-3 group">
              <div className="h-14 w-14 rounded-full bg-white border border-slate-200 flex items-center justify-center transition-all group-hover:border-slate-300 group-hover:shadow-sm">
                <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none">
                  <path d="M3.78 2.826a.6.6 0 0 0-.978.659l2.447 3.64a9.043 9.043 0 0 0-.803 1.23l-3.69-1.867a.6.6 0 1 0-.543 1.07l3.68 1.862a9.122 9.122 0 0 0-.33 1.413L.152 11.1a.6.6 0 1 0 .096 1.196l3.4-.265c.003.323.02.644.053.962l-3.324.603a.6.6 0 1 0 .215 1.18l3.316-.602c.09.392.202.777.333 1.154l-3.126 1.28a.6.6 0 1 0 .456 1.11l3.123-1.279c.19.402.403.79.64 1.163l-2.725 1.943a.6.6 0 1 0 .697.977l2.716-1.937c.277.379.578.74.902 1.08l-2.16 2.408a.6.6 0 0 0 .894.8l2.15-2.396c.357.334.738.645 1.14.931l-1.431 2.644a.6.6 0 0 0 1.053.57l1.424-2.63a9.15 9.15 0 0 0 1.278.519l-.566 2.883a.6.6 0 0 0 1.177.232l.565-2.875c.438.095.885.165 1.34.21l.183 2.966a.6.6 0 1 0 1.197-.074l-.183-2.966c.45-.026.893-.076 1.328-.149l.733 2.869a.6.6 0 1 0 1.162-.297l-.732-2.864a9.085 9.085 0 0 0 1.27-.47l1.4 2.627a.6.6 0 1 0 1.058-.563l-1.397-2.62c.4-.23.783-.485 1.147-.762l2.035 2.386a.6.6 0 0 0 .913-.782l-2.028-2.378c.356-.313.691-.65 1.003-1.008l2.556 1.896a.6.6 0 1 0 .713-.966l-2.544-1.888c.283-.385.544-.79.78-1.211l2.923 1.262a.6.6 0 1 0 .476-1.1l-2.913-1.258c.192-.432.36-.88.503-1.338l3.141.581a.6.6 0 0 0 .219-1.18l-3.131-.578c.102-.455.178-.92.23-1.393l3.292.086a.6.6 0 0 0 .031-1.2l-3.287-.086a9.15 9.15 0 0 0-.112-1.396l3.328-.388a.6.6 0 1 0-.14-1.192l-3.317.387a9.053 9.053 0 0 0-.4-1.307l3.223-.92a.6.6 0 0 0-.33-1.154l-3.207.916a9.1 9.1 0 0 0-.697-1.166l2.979-1.476a.6.6 0 1 0-.535-1.074l-2.963 1.468a9.058 9.058 0 0 0-.957-.97l2.592-1.969a.6.6 0 0 0-.727-.955l-2.575 1.955a9.076 9.076 0 0 0-1.17-.765l2.045-2.39a.6.6 0 0 0-.91-.78l-2.027 2.368a9.035 9.035 0 0 0-1.333-.487l1.363-2.65a.6.6 0 1 0-1.068-.55l-1.351 2.626a9.107 9.107 0 0 0-1.455-.185L12.602.322a.6.6 0 0 0-1.195.1l.125 2.963a9.095 9.095 0 0 0-1.462.203L9.17.68a.6.6 0 1 0-1.16.306l.896 2.896c-.48.154-.947.336-1.398.546L6.085 1.906a.6.6 0 1 0-1.023.625l1.42 2.516a9.095 9.095 0 0 0-1.25.811L3.78 2.826z" fill="#5E6AD2"/>
                </svg>
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Linear</span>
            </div>
            {/* GitHub */}
            <div className="flex flex-col items-center gap-3 group">
              <div className="h-14 w-14 rounded-full bg-white border border-slate-200 flex items-center justify-center transition-all group-hover:border-slate-300 group-hover:shadow-sm">
                <svg className="h-7 w-7" viewBox="0 0 24 24" fill="none">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" fill="#181717"/>
                </svg>
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">GitHub</span>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials - Love Letters Style */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="mb-16 text-center text-3xl font-light text-slate-900">
            Love Letters
          </h2>
          <div className="grid gap-12 md:grid-cols-3">
            {[
              {
                quote: "Corta spotted a blocker before anyone said it out loud.",
                author: "Engineering Lead",
              },
              {
                quote:
                  "I haven't manually updated a ticket in 2 weeks.",
                author: "Developer",
              },
              {
                quote:
                  "Our leadership now understands engineering without me writing a single report.",
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
                <p className="text-xs text-slate-400 font-light uppercase tracking-wider">{testimonial.author}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="bg-blue-600 py-24">
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
        </div>
      </section>
    </div>
  );
}
