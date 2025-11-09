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
import { loadSession, clearSession, AuthSession } from '../../lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type OAuthService = 'slack' | 'linear' | 'github';

interface OAuthStatus {
  connected: boolean;
  service: string;
  workspace?: string;
  connected_at?: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    const existing = loadSession();
    if (!existing) {
      router.replace('/login');
      return;
    }
    setSession(existing);
  }, [router]);

  const authHeaders = useMemo(() => {
    if (!session) return undefined;
    return {
      Authorization: `Bearer ${session.token}`,
    };
  }, [session]);

  useEffect(() => {
    if (error) {
      const timeout = setTimeout(() => setError(null), 4000);
      return () => clearTimeout(timeout);
    }
  }, [error]);

  useEffect(() => {
    if (statusMessage) {
      const timeout = setTimeout(() => setStatusMessage(null), 4000);
      return () => clearTimeout(timeout);
    }
  }, [statusMessage]);

  const slackStatus = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'slack'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/oauth/slack/status`, {
        headers: authHeaders,
      });
      return response.data;
    },
    enabled: !!authHeaders,
    retry: 1,
  });

  const linearStatus = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'linear'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/oauth/linear/status`, {
        headers: authHeaders,
      });
      return response.data;
    },
    enabled: !!authHeaders,
    retry: 1,
  });

  const githubStatus = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'github'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/oauth/github/status`, {
        headers: authHeaders,
      });
      return response.data;
    },
    enabled: !!authHeaders,
    retry: 1,
  });

  const connectMutation = useMutation({
    mutationFn: async (service: OAuthService) => {
      const redirectUri = `${window.location.origin}/oauth/callback/${service}`;
      const res = await axios.get(
        `${API_URL}/api/oauth/${service}/authorize`,
        {
          params: { redirect_uri: redirectUri },
          headers: authHeaders,
        }
      );
      const popup = window.open(
        res.data.auth_url,
        `${service}-auth`,
        'width=640,height=720'
      );

      if (!popup) {
        setError('Popup blocked. Please allow popups for this site and try again.');
        return;
      }

      const timer = window.setInterval(() => {
        if (popup.closed) {
          window.clearInterval(timer);
          queryClient.invalidateQueries({ queryKey: ['oauth', service] });
          setStatusMessage(`${capitalize(service)} connection updated.`);
        }
      }, 500);
    },
    onError: () => {
      setError('Failed to start OAuth flow. Check credentials and try again.');
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: async (service: OAuthService) => {
      await axios.delete(`${API_URL}/api/oauth/${service}/disconnect`, {
        headers: authHeaders,
      });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['oauth', variables] });
      setStatusMessage(`${capitalize(variables)} disconnected.`);
    },
    onError: () => {
      setError('Unable to disconnect service.');
    },
  });

  const ingestMutation = useMutation({
    mutationFn: async (service: OAuthService) => {
      await axios.post(
        `${API_URL}/api/workflows/ingest/${service}`,
        {},
        { headers: authHeaders }
      );
    },
    onSuccess: (_data, variables) => {
      setStatusMessage(`${capitalize(variables)} ingestion kicked off.`);
    },
    onError: () => {
      setError('Failed to trigger ingestion. Confirm the integration is connected.');
    },
  });

  const handleLogout = () => {
    clearSession();
    router.push('/login');
  };

  if (!session) {
    return null;
  }

  const services = [
    {
      key: 'slack' as const,
      title: 'Slack',
      description: 'Sync threads, DMs, and private channels where your team collaborates.',
      status: slackStatus,
    },
    {
      key: 'linear' as const,
      title: 'Linear',
      description: 'Keep tickets in sync, close loops, and surface stale work automatically.',
      status: linearStatus,
    },
    {
      key: 'github' as const,
      title: 'GitHub',
      description:
        'Track pull requests, reviews, and commits shaping your product every day.',
      status: githubStatus,
    },
  ];

  return (
    <div className="bg-slate-50 py-12">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">
              Welcome back, {session.email ?? 'PM'}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Manage your workspace integrations and trigger workflows on demand.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/docs"
              className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-brand-300 hover:text-brand-600"
            >
              View docs
            </Link>
            <button
              onClick={handleLogout}
              className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-slate-800"
            >
              Log out
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {statusMessage && (
          <div className="mb-6 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            {statusMessage}
          </div>
        )}

        {/* Integrations */}
        <section className="grid gap-6 lg:grid-cols-3">
          {services.map((service) => (
            <div
              key={service.key}
              className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-100"
            >
              <div>
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-slate-900">
                    {service.title}
                  </h2>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                      service.status.data?.connected
                        ? 'bg-green-100 text-green-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {service.status.data?.connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <p className="mt-2 text-sm text-slate-500">
                  {service.description}
                </p>
                {service.status.data?.connected && (
                  <p className="mt-3 text-xs text-slate-400">
                    Workspace: <span className="font-medium text-slate-600">{service.status.data.workspace}</span>
                  </p>
                )}
              </div>
              <div className="mt-6 flex flex-wrap gap-2">
                {service.status.data?.connected ? (
                  <>
                    <button
                      onClick={() => ingestMutation.mutate(service.key)}
                      className="flex-1 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
                    >
                      Run ingestion
                    </button>
                    <button
                      onClick={() => disconnectMutation.mutate(service.key)}
                      className="flex-1 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-600 hover:border-red-300"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => connectMutation.mutate(service.key)}
                    className="flex-1 rounded-md border border-brand-200 bg-brand-50 px-4 py-2 text-sm font-semibold text-brand-600 hover:border-brand-300"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>
          ))}
        </section>

        {/* Workflows */}
        <section className="mt-12">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900">Workflows</h2>
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Coming soon: schedule & configuration UI
            </span>
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {[
              {
                name: 'Daily standup',
                description:
                  'Generates a daily briefing of what shipped, ongoing work, and blockers across GitHub, Slack, and Linear.',
                endpoint: '/api/workflows/standup',
                actionLabel: 'View summary',
              },
              {
                name: 'Process inbox',
                description:
                  'Review messages and automatically create or update Linear tickets with AI assistance.',
                endpoint: '/api/workflows/process',
                actionLabel: 'Run (dry mode)',
              },
              {
                name: 'Move tickets',
                description:
                  'Review inactive work and move issues through the workflow with confidence scores.',
                endpoint: '/api/workflows/move-tickets',
                actionLabel: 'Run analysis',
              },
              {
                name: 'Weekly report',
                description:
                  'Summarize weekly accomplishments and send to stakeholders every Friday morning.',
                endpoint: null,
                actionLabel: 'Schedule soon',
              },
            ].map((workflow) => (
              <div
                key={workflow.name}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm shadow-slate-100"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">
                      {workflow.name}
                    </h3>
                    <p className="mt-2 text-sm text-slate-500">
                      {workflow.description}
                    </p>
                  </div>
                  <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-600">
                    AI powered
                  </span>
                </div>
                <div className="mt-4 flex gap-3 text-xs text-slate-400">
                  <span>Audit logs</span>
                  <span>Tenant aware</span>
                  <span>Background tasks</span>
                </div>
                <div className="mt-6">
                  {workflow.endpoint ? (
                    <button
                      onClick={async () => {
                        try {
                          await axios.post(
                            `${API_URL}${workflow.endpoint}`,
                            {},
                            { headers: authHeaders }
                          );
                          setStatusMessage(`${workflow.name} triggered.`);
                        } catch (err) {
                          setError(`Failed to run ${workflow.name.toLowerCase()}.`);
                        }
                      }}
                      className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
                    >
                      {workflow.actionLabel}
                    </button>
                  ) : (
                    <button
                      disabled
                      className="cursor-not-allowed rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-400"
                    >
                      {workflow.actionLabel}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function capitalize(text: string) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

