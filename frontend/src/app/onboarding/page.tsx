'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Code2, BarChart3, ArrowRight, Check } from 'lucide-react';
import { loadSession, completeOnboarding, fetchUserInfo } from '../../lib/auth';

export default function OnboardingPage() {
  const router = useRouter();
  const [selectedRole, setSelectedRole] = useState<'dev' | 'stakeholder' | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function checkOnboarding() {
      const session = loadSession();
      if (!session) {
        router.replace('/login');
        return;
      }

      const user = await fetchUserInfo();
      if (user?.onboarding_completed) {
        // Already completed, redirect to dashboard
        router.replace('/dashboard');
        return;
      }
      setChecking(false);
    }
    checkOnboarding();
  }, [router]);

  const handleContinue = async () => {
    if (!selectedRole) return;
    
    setLoading(true);
    const success = await completeOnboarding(selectedRole);
    
    if (success) {
      router.push('/dashboard');
    } else {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-6 py-16">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-slate-900">What's your role?</h1>
          <p className="mt-3 text-lg text-slate-500">
            This helps us show you the right dashboard. You can always switch later.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Developer Option */}
          <button
            onClick={() => setSelectedRole('dev')}
            className={`relative rounded-2xl border-2 p-8 text-left transition-all ${
              selectedRole === 'dev'
                ? 'border-violet-500 bg-violet-50 shadow-lg shadow-violet-500/10'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-md'
            }`}
          >
            {selectedRole === 'dev' && (
              <div className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-violet-500 text-white">
                <Check size={14} strokeWidth={3} />
              </div>
            )}
            <div className={`mb-4 inline-flex rounded-xl p-3 ${
              selectedRole === 'dev' ? 'bg-violet-100 text-violet-600' : 'bg-slate-100 text-slate-500'
            }`}>
              <Code2 size={28} />
            </div>
            <h3 className="text-xl font-semibold text-slate-900">I'm a Developer</h3>
            <p className="mt-2 text-sm text-slate-500">
              I'll set up the integrations, configure workflows, and manage the automation.
            </p>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                Connect Slack, Linear, GitHub
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                Configure workflow automations
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                View activity logs
              </li>
            </ul>
          </button>

          {/* Stakeholder Option */}
          <button
            onClick={() => setSelectedRole('stakeholder')}
            className={`relative rounded-2xl border-2 p-8 text-left transition-all ${
              selectedRole === 'stakeholder'
                ? 'border-violet-500 bg-violet-50 shadow-lg shadow-violet-500/10'
                : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-md'
            }`}
          >
            {selectedRole === 'stakeholder' && (
              <div className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-violet-500 text-white">
                <Check size={14} strokeWidth={3} />
              </div>
            )}
            <div className={`mb-4 inline-flex rounded-xl p-3 ${
              selectedRole === 'stakeholder' ? 'bg-violet-100 text-violet-600' : 'bg-slate-100 text-slate-500'
            }`}>
              <BarChart3 size={28} />
            </div>
            <h3 className="text-xl font-semibold text-slate-900">I'm a Stakeholder</h3>
            <p className="mt-2 text-sm text-slate-500">
              I want visibility into what my team is working on without the noise.
            </p>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                Weekly progress summaries
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                Team activity reports
              </li>
              <li className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-violet-500" />
                Invite team members
              </li>
            </ul>
          </button>
        </div>

        <div className="mt-10 flex justify-center">
          <button
            onClick={handleContinue}
            disabled={!selectedRole || loading}
            className="group flex items-center gap-2 rounded-xl bg-violet-600 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-violet-500/25 transition-all hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Setting up...' : 'Continue'}
            <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-slate-400">
          As the account owner, you can switch between views anytime.
        </p>
      </div>
    </div>
  );
}

