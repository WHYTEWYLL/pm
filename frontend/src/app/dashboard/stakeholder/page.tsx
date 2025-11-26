'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import Link from 'next/link';
import {
  BarChart3,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  MessageSquare,
  Users,
  Mail,
  Bell,
  UserPlus,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { loadSession, AuthSession, fetchUserInfo, getCurrentView, setCurrentView, UserInfo } from '../../../lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface NotificationSettings {
  weekly_email: boolean;
  slack_digest: boolean;
  blocker_alerts: boolean;
}

const DEFAULT_NOTIFICATIONS: NotificationSettings = {
  weekly_email: true,
  slack_digest: false,
  blocker_alerts: false,
};

interface ActivityMetrics {
  synced: number;
  linked: number;
  moved: number;
  created: number;
}

export default function StakeholderDashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [notifications, setNotifications] = useState<NotificationSettings>(DEFAULT_NOTIFICATIONS);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      const existing = loadSession();
      if (!existing) {
        router.replace('/login');
        return;
      }
      setSession(existing);

      const user = await fetchUserInfo();
      if (!user) {
        router.replace('/login');
        return;
      }

      if (!user.onboarding_completed) {
        router.replace('/onboarding');
        return;
      }

      setUserInfo(user);
      setChecking(false);
    }
    checkAuth();
  }, [router]);

  const authHeaders = useMemo(() => {
    if (!session) return undefined;
    return { Authorization: `Bearer ${session.token}` };
  }, [session]);

  // Activity metrics
  const activityQuery = useQuery<{ metrics: ActivityMetrics }>({
    queryKey: ['activity'],
    queryFn: async () => (await axios.get(`${API_URL}/api/settings/activity?days=7&limit=0`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  const metrics = activityQuery.data?.metrics ?? { synced: 0, linked: 0, moved: 0, created: 0 };

  const toggleNotification = (key: keyof NotificationSettings) => {
    setNotifications(prev => ({ ...prev, [key]: !prev[key] }));
    // TODO: Save to backend
  };

  if (!session || checking) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-violet-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-slate-100">
      <main className="mx-auto max-w-4xl px-6 py-10">
        {/* View Badge */}
        <div className="mb-6 flex items-center gap-3">
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-emerald-700">
            Stakeholder View
          </span>
          {(userInfo?.is_owner || userInfo?.permission === 'admin') && (
            <Link
              href="/dashboard"
              className="text-xs text-slate-400 hover:text-violet-600 hover:underline"
            >
              Switch to Dev View →
            </Link>
          )}
        </div>

        {/* Notifications */}
        {(error || statusMessage) && (
          <div className={`mb-8 flex items-center gap-3 rounded-xl border px-4 py-3 text-sm ${
            error ? 'border-red-200 bg-red-50 text-red-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'
          }`}>
            {error ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
            <span className="flex-1">{error || statusMessage}</span>
            <button
              onClick={() => { setError(null); setStatusMessage(null); }}
              className="font-medium hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* This Week Summary */}
        <section className="mb-10">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            This Week
          </h2>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
              <SummaryItem
                icon={<CheckCircle2 size={20} className="text-emerald-500" />}
                value={metrics.moved}
                label="Tickets completed"
              />
              <SummaryItem
                icon={<TrendingUp size={20} className="text-violet-500" />}
                value={metrics.created}
                label="New tickets"
              />
              <SummaryItem
                icon={<MessageSquare size={20} className="text-blue-500" />}
                value={metrics.linked}
                label="Conversations tracked"
              />
              <SummaryItem
                icon={<BarChart3 size={20} className="text-amber-500" />}
                value={metrics.synced}
                label="Messages synced"
              />
            </div>
          </div>
        </section>

        {/* Notifications Section */}
        <section className="mb-10">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Notifications
          </h2>
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <NotificationRow
              name="Weekly Email Summary"
              description="Get a Monday morning recap of last week's progress"
              icon={<Mail size={18} />}
              enabled={notifications.weekly_email}
              onToggle={() => toggleNotification('weekly_email')}
            />
            <NotificationRow
              name="Slack Digest"
              description="Daily summary posted to your Slack channel"
              icon={<MessageSquare size={18} />}
              enabled={notifications.slack_digest}
              onToggle={() => toggleNotification('slack_digest')}
            />
            <NotificationRow
              name="Blocker Alerts"
              description="Instant notification when blockers are detected"
              icon={<Bell size={18} />}
              enabled={notifications.blocker_alerts}
              onToggle={() => toggleNotification('blocker_alerts')}
              isLast
            />
          </div>
        </section>

        {/* Team Section */}
        <section className="mb-10">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Team
          </h2>
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-violet-100 text-violet-600">
                  <Users size={20} />
                </div>
                <div>
                  <p className="font-medium text-slate-900">{userInfo?.email}</p>
                  <p className="text-sm text-slate-500">Owner • {userInfo?.default_view === 'dev' ? 'Developer' : 'Stakeholder'}</p>
                </div>
              </div>
            </div>

            <div className="mt-6 border-t border-slate-100 pt-6">
              <button
                className="flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700"
              >
                <UserPlus size={16} />
                Invite Team Member
              </button>
              <p className="mt-3 text-xs text-slate-400">
                Invite developers or stakeholders to your team. Coming soon!
              </p>
            </div>
          </div>
        </section>

        {/* View Full Report Button */}
        <div className="flex justify-center">
          <Link
            href="/dashboard/reports"
            className="group flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700 hover:shadow-md"
          >
            <BarChart3 size={18} />
            View Full Report
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </main>
    </div>
  );
}

function SummaryItem({ icon, value, label }: { icon: React.ReactNode; value: number; label: string }) {
  return (
    <div className="text-center">
      <div className="mb-2 flex justify-center">{icon}</div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}

function NotificationRow({
  name,
  description,
  icon,
  enabled,
  onToggle,
  isLast = false,
}: {
  name: string;
  description: string;
  icon: React.ReactNode;
  enabled: boolean;
  onToggle: () => void;
  isLast?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between px-5 py-4 ${!isLast ? 'border-b border-slate-100' : ''}`}>
      <div className="flex items-center gap-4">
        <div className={`rounded-lg p-2 ${enabled ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'}`}>
          {icon}
        </div>
        <div>
          <h4 className="font-medium text-slate-900">{name}</h4>
          <p className="text-sm text-slate-500">{description}</p>
        </div>
      </div>
      <button
        onClick={onToggle}
        className={`relative h-7 w-12 rounded-full transition-colors ${
          enabled ? 'bg-emerald-500' : 'bg-slate-200'
        }`}
      >
        <span
          className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-all ${
            enabled ? 'left-6' : 'left-1'
          }`}
        />
      </button>
    </div>
  );
}

