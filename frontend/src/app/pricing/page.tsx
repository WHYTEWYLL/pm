"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loadSession } from "../../lib/auth";
import { createCheckoutSession } from "../../lib/subscription";

// These should be set in your Stripe dashboard and passed via environment variables
// For now, you'll need to replace these with your actual Stripe Price IDs
const STARTER_PRICE_ID = process.env.NEXT_PUBLIC_STRIPE_STARTER_PRICE_ID || "";
const SCALE_PRICE_ID = process.env.NEXT_PUBLIC_STRIPE_SCALE_PRICE_ID || "";

export default function PricingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (tier: "starter" | "scale") => {
    const session = loadSession();
    if (!session) {
      router.push("/login?redirect=/pricing");
      return;
    }

    const priceId = tier === "starter" ? STARTER_PRICE_ID : SCALE_PRICE_ID;
    
    if (!priceId) {
      setError(
        "Stripe price ID not configured. Please set NEXT_PUBLIC_STRIPE_STARTER_PRICE_ID and NEXT_PUBLIC_STRIPE_SCALE_PRICE_ID environment variables."
      );
      return;
    }

    setLoading(tier);
    setError(null);

    try {
      const checkoutUrl = await createCheckoutSession(priceId);
      // Redirect to Stripe Checkout
      window.location.href = checkoutUrl;
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create checkout session");
      setLoading(null);
    }
  };

  return (
    <div className="bg-slate-50 py-20">
      <div className="mx-auto max-w-5xl px-6">
        <div className="text-center">
          <h1 className="text-4xl font-semibold text-slate-900">Pricing</h1>
          <p className="mt-3 text-lg text-slate-600">
            Simple plans that scale with your engineering organization.
          </p>
          <p className="mt-2 text-sm text-brand-600 font-medium">
            🎉 Start with a 7-day free trial - no credit card required
          </p>
        </div>
        {error && (
          <div className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-semibold text-slate-900">Starter</h2>
            <p className="mt-3 text-sm text-slate-600">
              Perfect for seed-stage teams getting their PM workflows under control.
            </p>
            <div className="mt-6 text-3xl font-bold text-slate-900">
              $99 <span className="text-base font-medium text-slate-500">/ month</span>
            </div>
            <ul className="mt-6 space-y-3 text-sm text-slate-600">
              <li>• Up to 10 active engineers</li>
              <li>• Slack + Linear integrations</li>
              <li>• Daily standup and ticket hygiene workflows</li>
              <li>• Decision logging & audit trails</li>
            </ul>
            <button
              onClick={() => handleSubscribe("starter")}
              disabled={loading !== null}
              className="mt-8 rounded-md bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading === "starter" ? "Loading..." : "Subscribe"}
            </button>
          </div>
          <div className="flex flex-col rounded-2xl border border-brand-200 bg-white p-8 shadow-lg shadow-brand-100">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold text-slate-900">Scale</h2>
              <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
                Most popular
              </span>
            </div>
            <p className="mt-3 text-sm text-slate-600">
              For product teams managing multiple squads with enterprise-grade guardrails.
            </p>
            <div className="mt-6 text-3xl font-bold text-slate-900">
              $249 <span className="text-base font-medium text-slate-500">/ month</span>
            </div>
            <ul className="mt-6 space-y-3 text-sm text-slate-600">
              <li>• Everything in Starter</li>
              <li>• GitHub ingestion and PR insights</li>
              <li>• Weekly wins digest + incident retros</li>
              <li>• Priority support & onboarding</li>
              <li>• Stripe-powered billing & invoicing</li>
            </ul>
            <button
              onClick={() => handleSubscribe("scale")}
              disabled={loading !== null}
              className="mt-8 rounded-md bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading === "scale" ? "Loading..." : "Subscribe"}
            </button>
          </div>
        </div>
        <div className="mt-10 rounded-xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
          Need custom pricing for multi-tenant deployments or SOC2 requirements? Contact{" "}
          <a className="text-brand-600" href="mailto:sales@example.com">
            sales@example.com
          </a>
          .
        </div>
      </div>
    </div>
  );
}

