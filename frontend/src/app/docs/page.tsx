export default function DocsPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-20">
      <h1 className="text-4xl font-semibold text-slate-900">Documentation</h1>
      <p className="mt-4 text-slate-600">
        Full docs are coming soon. In the meantime, review the README in the repository or contact
        support for onboarding help.
      </p>
      <div className="mt-10 space-y-6">
        <section>
          <h2 className="text-2xl font-semibold text-slate-900">Getting Started</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            1. Create an account and tenant. 2. Connect Slack, Linear, and GitHub using OAuth. 3.
            Configure schedules for standups, reminders, and ticket automation. 4. Review decision
            logs to monitor AI reasoning.
          </p>
        </section>
        <section>
          <h2 className="text-2xl font-semibold text-slate-900">API Endpoints</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Explore the auto-generated API reference at <code className="rounded bg-slate-100 px-1">/docs</code> on
            the backend deployment to test endpoints interactively.
          </p>
        </section>
      </div>
    </div>
  );
}

