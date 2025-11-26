'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import axios from 'axios';
import Link from 'next/link';
import { 
  CheckCircle2, 
  AlertCircle, 
  Github, 
  Slack, 
  Trello,
  ArrowRight, 
  RefreshCw, 
  Link2,
  GitPullRequest,
  FileText,
  Send,
  Activity
} from 'lucide-react';
import { loadSession, AuthSession, fetchUserInfo, getCurrentView, setCurrentView, UserInfo } from '../../lib/auth';
import { getSubscriptionStatus, SubscriptionStatus } from '../../lib/subscription';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type OAuthService = 'slack' | 'linear' | 'github';

interface OAuthStatus {
  connected: boolean;
  service: string;
  workspace?: string;
  connected_at?: string;
}

interface WorkflowSettings {
  auto_sync: boolean;
  link_conversations: boolean;
  ticket_status_updates: boolean;
  daily_standup: boolean;
  create_tickets: boolean;
}

interface ActivityMetrics {
  synced: number;
  linked: number;
  moved: number;
  created: number;
}

interface ActivityResponse {
  items: any[];
  metrics: ActivityMetrics;
  has_more: boolean;
}

const DEFAULT_WORKFLOWS: WorkflowSettings = {
  auto_sync: true,
  link_conversations: true,
  ticket_status_updates: false,
  daily_standup: false,
  create_tickets: false,
};

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  // --- Auth & Effects ---
  useEffect(() => {
    async function checkAuth() {
      const existing = loadSession();
      if (!existing) {
        router.replace('/login');
        return;
      }
      setSession(existing);

      // Fetch user info to check onboarding and view
      const user = await fetchUserInfo();
      if (!user) {
        router.replace('/login');
        return;
      }

      // Redirect to onboarding if not completed
      if (!user.onboarding_completed) {
        router.replace('/onboarding');
        return;
      }

      // Set the view from user's preference if not already set
      const currentView = getCurrentView();
      if (!currentView || currentView !== user.default_view) {
        setCurrentView(user.default_view);
      }

      // Redirect stakeholders to their dashboard
      if (user.default_view === 'stakeholder') {
        router.replace('/dashboard/stakeholder');
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

  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;
      const payload = event.data;
      if (payload?.type === 'oauth-complete' && payload?.service) {
        queryClient.invalidateQueries({ queryKey: ['oauth', payload.service] });
        if (payload.success) {
          setStatusMessage(`${capitalize(payload.service)} connected successfully.`);
        } else if (payload.error) {
          setError(`Failed to connect ${payload.service}: ${payload.error}`);
        }
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [queryClient]);

  // --- Queries ---
  const slackStatus = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'slack'],
    queryFn: async () => (await axios.get(`${API_URL}/api/oauth/slack/status`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  const linearStatus = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'linear'],
    queryFn: async () => (await axios.get(`${API_URL}/api/oauth/linear/status`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  const githubStatus = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'github'],
    queryFn: async () => (await axios.get(`${API_URL}/api/oauth/github/status`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  const subscriptionStatus = useQuery<SubscriptionStatus>({
    queryKey: ['subscription'],
    queryFn: getSubscriptionStatus,
    enabled: !!session,
  });

  // Workflow settings
  const workflowsQuery = useQuery<WorkflowSettings>({
    queryKey: ['workflows'],
    queryFn: async () => (await axios.get(`${API_URL}/api/settings/workflows`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  // Activity metrics
  const activityQuery = useQuery<ActivityResponse>({
    queryKey: ['activity'],
    queryFn: async () => (await axios.get(`${API_URL}/api/settings/activity?days=7&limit=0`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  const workflows = workflowsQuery.data ?? DEFAULT_WORKFLOWS;
  const metrics = activityQuery.data?.metrics ?? { synced: 0, linked: 0, moved: 0, created: 0 };

  // --- Mutations ---
  const connectMutation = useMutation({
    mutationFn: async (service: OAuthService) => {
      const redirectUri = `${window.location.origin}/oauth/callback/${service}`;
      const res = await axios.get(`${API_URL}/api/oauth/${service}/authorize`, {
        params: { redirect_uri: redirectUri },
        headers: authHeaders,
      });
      const popup = window.open(res.data.auth_url, `${service}-auth`, 'width=640,height=720');
      if (!popup) setError('Popup blocked. Allow popups and try again.');
    },
  });

  const workflowMutation = useMutation({
    mutationFn: async (newSettings: WorkflowSettings) => {
      await axios.put(`${API_URL}/api/settings/workflows`, newSettings, { headers: authHeaders });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: () => {
      setError('Failed to save workflow settings.');
    },
  });

  const toggleWorkflow = (key: keyof WorkflowSettings) => {
    const newSettings = { ...workflows, [key]: !workflows[key] };
    workflowMutation.mutate(newSettings);
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
          <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-violet-700">
            Dev View
          </span>
          {userInfo?.is_owner && (
            <Link
              href="/dashboard/stakeholder"
              className="text-xs text-slate-400 hover:text-violet-600 hover:underline"
            >
              Switch to Stakeholder View →
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

        {/* Integrations Section */}
        <section className="mb-10">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Integrations
          </h2>
          <div className="grid grid-cols-3 gap-4">
            <IntegrationCard
              name="Slack"
              description="Read conversations"
              icon={<Slack size={24} />}
              connected={!!slackStatus.data?.connected}
              loading={slackStatus.isLoading}
              onConnect={() => connectMutation.mutate('slack')}
            />
            <IntegrationCard
              name="Linear"
              description="Manage tickets"
              icon={<Trello size={24} />}
              connected={!!linearStatus.data?.connected}
              loading={linearStatus.isLoading}
              onConnect={() => connectMutation.mutate('linear')}
            />
            <IntegrationCard
              name="GitHub"
              description="Track PRs & issues"
              icon={<Github size={24} />}
              connected={!!githubStatus.data?.connected}
              loading={githubStatus.isLoading}
              onConnect={() => connectMutation.mutate('github')}
              badge="Scale"
            />
          </div>
        </section>

        {/* Workflows Section */}
        <section className="mb-10">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Workflows
          </h2>
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <WorkflowRow
              name="Auto-Sync"
              description="Pull messages & tickets every hour"
              icon={<RefreshCw size={18} />}
              enabled={workflows.auto_sync}
              onToggle={() => toggleWorkflow('auto_sync')}
            />
            <WorkflowRow
              name="Link Conversations"
              description="Match Slack messages to Linear tickets"
              icon={<Link2 size={18} />}
              enabled={workflows.link_conversations}
              onToggle={() => toggleWorkflow('link_conversations')}
            />
            <WorkflowRow
              name="Ticket Status Updates"
              description="Auto-move tickets based on conversation context"
              icon={<GitPullRequest size={18} />}
              enabled={workflows.ticket_status_updates}
              onToggle={() => toggleWorkflow('ticket_status_updates')}
            />
            <WorkflowRow
              name="Daily Standup"
              description="Post summary to Slack each morning"
              icon={<Send size={18} />}
              enabled={workflows.daily_standup}
              onToggle={() => toggleWorkflow('daily_standup')}
            />
            <WorkflowRow
              name="Create Tickets"
              description="Auto-create tickets from untracked conversations"
              icon={<FileText size={18} />}
              enabled={workflows.create_tickets}
              onToggle={() => toggleWorkflow('create_tickets')}
              isLast
            />
          </div>
        </section>

        {/* Metrics Section */}
        <section className="mb-10">
          <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-400">
            Last 7 Days
          </h2>
          <div className="grid grid-cols-4 gap-4">
            <MetricCard label="Synced" value={metrics.synced} color="slate" />
            <MetricCard label="Linked" value={metrics.linked} color="violet" />
            <MetricCard label="Moved" value={metrics.moved} color="amber" />
            <MetricCard label="Created" value={metrics.created} color="emerald" />
          </div>
        </section>

        {/* Activity Log Button */}
        <div className="flex justify-center">
          <Link
            href="/dashboard/activity"
            className="group flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-medium text-slate-700 shadow-sm transition-all hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700 hover:shadow-md"
          >
            <Activity size={18} />
            View Activity Log
            <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </main>
    </div>
  );
}

// --- Subcomponents ---

function IntegrationCard({ 
  name, 
  description, 
  icon, 
  connected, 
  loading,
  onConnect,
  badge 
}: { 
  name: string; 
  description: string; 
  icon: React.ReactNode; 
  connected: boolean;
  loading: boolean;
  onConnect: () => void;
  badge?: string;
}) {
  return (
    <div className={`relative rounded-2xl border p-5 transition-all ${
      connected 
        ? 'border-emerald-200 bg-gradient-to-br from-emerald-50 to-white' 
        : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'
    }`}>
      {badge && (
        <span className="absolute right-3 top-3 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-700">
          {badge}
        </span>
      )}
      <div className={`mb-3 inline-flex rounded-xl p-2.5 ${
        connected ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'
      }`}>
        {icon}
      </div>
      <h3 className="font-semibold text-slate-900">{name}</h3>
      <p className="mt-0.5 text-sm text-slate-500">{description}</p>
      
      {loading ? (
        <div className="mt-4 h-8 w-20 animate-pulse rounded-lg bg-slate-100" />
      ) : connected ? (
        <div className="mt-4 flex items-center gap-1.5 text-sm font-medium text-emerald-600">
          <CheckCircle2 size={16} />
          Connected
        </div>
      ) : (
        <button
          onClick={onConnect}
          className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800"
        >
          Connect
        </button>
      )}
    </div>
  );
}

function WorkflowRow({ 
  name, 
  description, 
  icon, 
  enabled, 
  onToggle,
  isLast = false 
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
        <div className={`rounded-lg p-2 ${enabled ? 'bg-violet-100 text-violet-600' : 'bg-slate-100 text-slate-400'}`}>
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
          enabled ? 'bg-violet-600' : 'bg-slate-200'
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

function MetricCard({ 
  label, 
  value, 
  color 
}: { 
  label: string; 
  value: number;
  color: 'slate' | 'violet' | 'amber' | 'emerald';
}) {
  const colorClasses = {
    slate: 'bg-slate-50 border-slate-200',
    violet: 'bg-violet-50 border-violet-200',
    amber: 'bg-amber-50 border-amber-200',
    emerald: 'bg-emerald-50 border-emerald-200',
  };
  
  const textClasses = {
    slate: 'text-slate-900',
    violet: 'text-violet-900',
    amber: 'text-amber-900',
    emerald: 'text-emerald-900',
  };

  return (
    <div className={`rounded-2xl border p-5 text-center ${colorClasses[color]}`}>
      <p className={`text-3xl font-bold ${textClasses[color]}`}>{value}</p>
      <p className="mt-1 text-sm font-medium text-slate-500">{label}</p>
    </div>
  );
}

function capitalize(text: string) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
