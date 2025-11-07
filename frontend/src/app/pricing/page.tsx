export default function PricingPage() {
  return (
    <div className="bg-slate-50 py-20">
      <div className="mx-auto max-w-5xl px-6">
        <div className="text-center">
          <h1 className="text-4xl font-semibold text-slate-900">Pricing</h1>
          <p className="mt-3 text-lg text-slate-600">
            Simple plans that scale with your engineering organization.
          </p>
        </div>
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

