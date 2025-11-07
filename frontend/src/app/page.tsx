import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      {/* Hero */}
      <section className="relative">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-brand-50 via-white to-slate-100" />
        <div className="mx-auto flex max-w-6xl flex-col-reverse items-center gap-16 px-6 py-20 lg:flex-row lg:py-28">
          <div className="max-w-2xl text-center lg:text-left">
            <span className="inline-flex items-center rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700">
              AI copilots for engineering teams
            </span>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Orchestrate your PM workflows with{" "}
              <span className="text-brand-600">real-time AI assistance</span>
            </h1>
            <p className="mt-6 text-lg leading-8 text-slate-600">
              PM Assistant ingests Slack conversations, GitHub activity, and
              Linear tickets every day. The result: daily standups, automated
              ticket updates, and weekly summaries delivered without manual
              chasing.
            </p>
            <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start">
              <Link
                href="/register"
                className="w-full rounded-md bg-brand-600 px-6 py-3 text-center text-base font-semibold text-white shadow-lg shadow-brand-200 transition hover:bg-brand-700 sm:w-auto"
              >
                Start free trial
              </Link>
              <Link
                href="/login"
                className="w-full rounded-md border border-slate-200 px-6 py-3 text-center text-base font-semibold text-slate-700 transition hover:border-brand-300 hover:text-brand-600 sm:w-auto"
              >
                Log in to dashboard
              </Link>
            </div>
            <div className="mt-6 flex items-center justify-center gap-6 text-sm text-slate-500 lg:justify-start">
              <div>
                <span className="font-semibold text-slate-700">24h</span> data refresh
              </div>
              <div>
                <span className="font-semibold text-slate-700">3</span> integrations today
              </div>
              <div>
                <span className="font-semibold text-slate-700">100%</span> audit trail
              </div>
            </div>
          </div>
          <div className="relative w-full max-w-xl">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl shadow-brand-100/50">
              <div className="mb-4 flex items-center justify-between border-b border-slate-200 pb-4">
                <div>
                  <p className="text-sm font-medium text-brand-600">Daily Standup</p>
                  <p className="text-xs text-slate-500">Generated 8:45 AM • Slack</p>
                </div>
                <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600">
                  Today
                </span>
              </div>
              <ul className="space-y-4 text-sm text-slate-600">
                <li className="rounded-lg border border-slate-100 bg-slate-50/80 p-3">
                  Ship checkout telemetry fix • owner <span className="font-semibold">Sofia</span>
                  <div className="mt-1 text-xs text-slate-500">
                    Detected from GitHub PR #421 and Slack thread in #reliability
                  </div>
                </li>
                <li className="rounded-lg border border-slate-100 bg-slate-50/80 p-3">
                  Prepare RFC for async notifications • owner{" "}
                  <span className="font-semibold">Anish</span>
                  <div className="mt-1 text-xs text-slate-500">
                    Linear issue TSK-234 linked to product channel discussion
                  </div>
                </li>
                <li className="rounded-lg border border-slate-100 bg-slate-50/80 p-3">
                  Close stale tickets in Triage column • owner{" "}
                  <span className="font-semibold">Maria</span>
                  <div className="mt-1 text-xs text-slate-500">
                    3 issues identified with no activity in 7 days
                  </div>
                </li>
              </ul>
              <div className="mt-6 rounded-md bg-brand-50 px-4 py-3 text-xs text-brand-700">
                All actions are logged in tenant-specific audit trail with AI reasoning and confidence
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="border-t border-slate-200 bg-white py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-sm font-semibold uppercase tracking-wide text-brand-600">
            Built for Staff+ PMs and Engineering Leaders
          </h2>
          <p className="mt-4 text-center text-3xl font-semibold text-slate-900">
            A shared brain that turns conversations into action
          </p>
          <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "Daily standup briefs",
                description:
                  "Summaries of what each engineer shipped, plans, and blockers pulled from GitHub, Slack, and Linear.",
              },
              {
                title: "Ticket hygiene, automated",
                description:
                  "Move Linear issues across states, close duplicates, and open follow-ups based on AI tagging of conversations.",
              },
              {
                title: "Friday wins digest",
                description:
                  "Share a digest of the week's top accomplishments with leadership, generated automatically every Friday morning.",
              },
              {
                title: "Decision logging",
                description:
                  "Every AI action is recorded with reasoning, confidence, and source messages for governance and trust.",
              },
              {
                title: "Multi-tenant by design",
                description:
                  "Onboard multiple orgs, each with isolated databases, encrypted tokens, and per-tenant configuration.",
              },
              {
                title: "Zapier-grade integrations",
                description:
                  "OAuth flows for Slack, Linear, and GitHub so your teams stay secure and in control of access.",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="rounded-xl border border-slate-200 bg-slate-50/60 p-6 shadow-sm shadow-slate-100"
              >
                <h3 className="text-lg font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Workflows */}
      <section id="workflows" className="bg-slate-900 py-20">
        <div className="mx-auto max-w-6xl px-6 text-slate-100">
          <div className="flex flex-col gap-12 lg:flex-row lg:items-start">
            <div className="w-full lg:w-1/3">
              <h2 className="text-3xl font-semibold">
                Automate the boring, stay focused on outcomes
              </h2>
              <p className="mt-4 text-slate-300">
                Activate the workflows you need, customize schedules, and trust the AI to do the heavy
                lifting with clear audit logs.
              </p>
            </div>
            <div className="grid w-full gap-6 lg:w-2/3">
              {[
                {
                  name: "Standup sync",
                  description:
                    "Digest daily commits, PR comments, and Slack threads into actionable to-do lists.",
                },
                {
                  name: "Message → Ticket",
                  description:
                    "Turn noisy discussions into Linear issues with owner assignment, due dates, and context automatically filled in.",
                },
                {
                  name: "Weekly recap",
                  description:
                    "Friday morning summary of shipped work, resolved incidents, and high-signal conversations.",
                },
                {
                  name: "Health guardrails",
                  description:
                    "Alert when tickets stall, conversations go unanswered, or PRs lack owner follow-up.",
                },
              ].map((workflow) => (
                <div key={workflow.name} className="rounded-lg border border-white/10 bg-white/5 p-5">
                  <h3 className="text-xl font-semibold text-white">{workflow.name}</h3>
                  <p className="mt-2 text-sm text-slate-200">{workflow.description}</p>
                  <div className="mt-4 flex items-center gap-3 text-xs text-slate-400">
                    <span className="rounded-full bg-white/10 px-3 py-1">Uses AI</span>
                    <span className="rounded-full bg-white/10 px-3 py-1">Full audit log</span>
                    <span className="rounded-full bg-white/10 px-3 py-1">Tenant scoped</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-4xl rounded-2xl border border-brand-100 bg-brand-50 px-10 py-12 text-center shadow-lg shadow-brand-200/40">
          <h2 className="text-3xl font-semibold text-slate-900">
            Ready to launch an AI-powered PM assistant for your org?
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Connect Slack, Linear, and GitHub with secure OAuth, then let the assistant run daily
            workflows while keeping humans in the loop.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/register"
              className="w-full rounded-md bg-brand-600 px-6 py-3 text-center text-base font-semibold text-white shadow-lg hover:bg-brand-700 sm:w-auto"
            >
              Create your tenant
            </Link>
            <Link
              href="/docs"
              className="w-full rounded-md border border-brand-200 px-6 py-3 text-center text-base font-semibold text-brand-600 hover:border-brand-300 sm:w-auto"
            >
              Explore the docs
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

