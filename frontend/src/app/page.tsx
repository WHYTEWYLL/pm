import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      {/* Hero Section */}
      <section className="relative">
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-brand-50 via-white to-slate-100" />
        <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
          <div className="text-center">
            <h1 className="text-5xl font-bold tracking-tight text-slate-900 sm:text-6xl lg:text-7xl">
              Corta.ai
            </h1>
            <p className="mt-6 text-3xl font-semibold text-slate-700 sm:text-4xl lg:text-5xl">
              Your Automatic Project Manager
            </p>
            <p className="mt-6 text-xl text-slate-600 sm:text-2xl">
              Alignment for the team. Clarity for stakeholders.
            </p>
            <p className="mt-4 text-lg font-medium text-brand-600">
              100% automated.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/register"
                className="w-full rounded-md bg-brand-600 px-8 py-4 text-center text-base font-semibold text-white shadow-lg shadow-brand-200 transition hover:bg-brand-700 sm:w-auto"
              >
                For Teams
              </Link>
              <Link
                href="/register"
                className="w-full rounded-md border-2 border-brand-600 px-8 py-4 text-center text-base font-semibold text-brand-600 transition hover:bg-brand-50 sm:w-auto"
              >
                For Stakeholders
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Key Message Banner */}
      <section className="border-y border-slate-200 bg-slate-900 py-8">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="text-lg font-medium text-white sm:text-xl">
            <span className="font-semibold">Corta is not a chatbot.</span> Cut the noise you and with you.
          </p>
          <p className="mt-2 text-lg text-slate-300 sm:text-xl">
            Corta is the operating system of product execution.
          </p>
          <p className="mt-2 text-sm text-slate-400">
            It works continuously, automatically, and without prompting.
          </p>
        </div>
      </section>

      {/* Split Section: Team Mode & Stakeholder Mode */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-8 lg:grid-cols-2">
            {/* Team Mode */}
            <div className="rounded-2xl border-2 border-brand-200 bg-gradient-to-br from-brand-50 to-white p-8 shadow-lg">
              <div className="mb-6">
                <h2 className="text-3xl font-bold text-slate-900">Team Mode</h2>
                <p className="mt-2 text-lg text-slate-600">
                  Keeps everyone aligned
                </p>
              </div>
              <ul className="space-y-4 text-slate-700">
                <li className="flex items-start gap-3">
                  <svg
                    className="mt-1 h-5 w-5 flex-shrink-0 text-brand-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>Tracks progress</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg
                    className="mt-1 h-5 w-5 flex-shrink-0 text-brand-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>Cleans up tickets</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg
                    className="mt-1 h-5 w-5 flex-shrink-0 text-brand-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>Ensures no one is blocked</span>
                </li>
              </ul>
              <div className="mt-8">
                <Link
                  href="/register"
                  className="inline-block rounded-md bg-brand-600 px-6 py-3 text-base font-semibold text-white hover:bg-brand-700"
                >
                  Learn More
                </Link>
              </div>
            </div>

            {/* Stakeholder Mode */}
            <div className="rounded-2xl border-2 border-slate-200 bg-gradient-to-br from-slate-50 to-white p-8 shadow-lg">
              <div className="mb-6">
                <h2 className="text-3xl font-bold text-slate-900">Stakeholder Mode</h2>
                <p className="mt-2 text-lg text-slate-600">
                  Weekly updates
                </p>
              </div>
              <ul className="space-y-4 text-slate-700">
                <li className="flex items-start gap-3">
                  <svg
                    className="mt-1 h-5 w-5 flex-shrink-0 text-slate-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>Executive summaries</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg
                    className="mt-1 h-5 w-5 flex-shrink-0 text-slate-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>Context-rich progress reports</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg
                    className="mt-1 h-5 w-5 flex-shrink-0 text-slate-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span>Audience-aware communication</span>
                </li>
              </ul>
              <div className="mt-8">
                <Link
                  href="/register"
                  className="inline-block rounded-md border-2 border-slate-300 bg-white px-6 py-3 text-base font-semibold text-slate-700 hover:border-slate-400 hover:bg-slate-50"
                >
                  Learn More
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How Corta Works */}
      <section className="bg-slate-50 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-slate-900 sm:text-5xl">
              How Corta Works
            </h2>
            <p className="mt-4 text-xl font-medium text-brand-600">
              The Magic
            </p>
            <p className="mt-6 text-lg text-slate-600 sm:text-xl">
              It observes. It organizes. It communicates. Automatically.
            </p>
            <p className="mt-4 text-lg font-semibold text-slate-700">
              No prompts. No micromanagement.
            </p>
          </div>

          <div className="mt-12 rounded-2xl border border-slate-200 bg-white p-8 shadow-lg lg:p-12">
            <div className="space-y-6 text-center">
              <p className="text-lg text-slate-700">
                Corta plugs into the tools your team already uses
              </p>
              <p className="text-lg text-slate-700">
                and behaves like the PM that never forgets anything.
              </p>
              <p className="text-xl font-semibold text-slate-900">
                Let everyone's work speaks for themselves.
              </p>
            </div>

            {/* Integration Icons */}
            <div className="mt-12 flex flex-wrap items-center justify-center gap-8">
              {["Slack", "Linear", "GitHub"].map((tool) => (
                <div
                  key={tool}
                  className="flex flex-col items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-6 py-4"
                >
                  <div className="h-12 w-12 rounded-full bg-brand-100"></div>
                  <span className="text-sm font-medium text-slate-700">{tool}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="bg-white py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="mb-12 text-center text-3xl font-bold text-slate-900">
            What Teams Are Saying
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
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
                  "Our engineers finally stay in sync without me manual pinging.",
                author: "Tech Lead",
              },
            ].map((testimonial, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 bg-slate-50 p-6 shadow-sm"
              >
                <p className="text-lg font-medium text-slate-900">
                  "{testimonial.quote}"
                </p>
                <p className="mt-4 text-sm text-slate-600">— {testimonial.author}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Call to Action */}
      <section className="bg-gradient-to-br from-brand-600 to-brand-700 py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-4xl font-bold text-white sm:text-5xl">
            Get early access
          </h2>
          <p className="mt-6 text-xl text-brand-100">
            Corta handles the work behind the work.
          </p>
          <div className="mt-10">
            <Link
              href="/register"
              className="inline-block rounded-md bg-white px-8 py-4 text-base font-semibold text-brand-600 shadow-lg transition hover:bg-slate-50"
            >
              Start Free Trial
            </Link>
          </div>
          <p className="mt-6 text-sm text-brand-200">
            No credit card required • 7-day free trial
          </p>
        </div>
      </section>

      {/* Footer Message */}
      <section className="border-t border-slate-200 bg-slate-900 py-8">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <p className="text-sm text-slate-400">
            <span className="font-semibold text-white">Corta is not a chatbot.</span>{" "}
            Cut the noise you and with you.
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Corta is the operating system of product execution.
          </p>
        </div>
      </section>
    </div>
  );
}
