'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface OAuthStatus {
  connected: boolean;
  service: string;
  workspace?: string;
  connected_at?: string;
}

export default function Dashboard() {
  const [tenantId, setTenantId] = useState<string>('');

  useEffect(() => {
    // Get tenant ID from cookie or localStorage
    const stored = localStorage.getItem('tenant_id') || 'dev-tenant-1';
    setTenantId(stored);
  }, []);

  const { data: slackStatus } = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'slack', tenantId],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/api/oauth/slack/status`, {
        headers: { Authorization: `Bearer ${tenantId}` },
      });
      return res.data;
    },
    enabled: !!tenantId,
  });

  const { data: linearStatus } = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'linear', tenantId],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/api/oauth/linear/status`, {
        headers: { Authorization: `Bearer ${tenantId}` },
      });
      return res.data;
    },
    enabled: !!tenantId,
  });

  const { data: githubStatus } = useQuery<OAuthStatus>({
    queryKey: ['oauth', 'github', tenantId],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/api/oauth/github/status`, {
        headers: { Authorization: `Bearer ${tenantId}` },
      });
      return res.data;
    },
    enabled: !!tenantId,
  });

  const connectMutation = useMutation({
    mutationFn: async (service: string) => {
      const redirectUri = `${window.location.origin}/oauth/callback/${service}`;
      const res = await axios.get(`${API_URL}/api/oauth/${service}/authorize`, {
        params: { redirect_uri: redirectUri },
        headers: { Authorization: `Bearer ${tenantId}` },
      });
      window.location.href = res.data.auth_url;
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: async (service: string) => {
      await axios.delete(`${API_URL}/api/oauth/${service}/disconnect`, {
        headers: { Authorization: `Bearer ${tenantId}` },
      });
    },
  });

  const ingestMutation = useMutation({
    mutationFn: async (service: string) => {
      await axios.post(`${API_URL}/api/workflows/ingest/${service}`, {}, {
        headers: { Authorization: `Bearer ${tenantId}` },
      });
    },
  });

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">PM Assistant Dashboard</h1>

        {/* OAuth Connections */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Connected Services</h2>
          
          <div className="space-y-4">
            {/* Slack */}
            <div className="flex items-center justify-between p-4 border rounded">
              <div>
                <h3 className="font-medium">Slack</h3>
                <p className="text-sm text-gray-500">
                  {slackStatus?.connected
                    ? `Connected to ${slackStatus.workspace}`
                    : 'Not connected'}
                </p>
              </div>
              <div className="flex gap-2">
                {slackStatus?.connected ? (
                  <>
                    <button
                      onClick={() => ingestMutation.mutate('slack')}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Ingest
                    </button>
                    <button
                      onClick={() => disconnectMutation.mutate('slack')}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => connectMutation.mutate('slack')}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>

            {/* Linear */}
            <div className="flex items-center justify-between p-4 border rounded">
              <div>
                <h3 className="font-medium">Linear</h3>
                <p className="text-sm text-gray-500">
                  {linearStatus?.connected
                    ? `Connected to ${linearStatus.workspace}`
                    : 'Not connected'}
                </p>
              </div>
              <div className="flex gap-2">
                {linearStatus?.connected ? (
                  <>
                    <button
                      onClick={() => ingestMutation.mutate('linear')}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Ingest
                    </button>
                    <button
                      onClick={() => disconnectMutation.mutate('linear')}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => connectMutation.mutate('linear')}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>

            {/* GitHub */}
            <div className="flex items-center justify-between p-4 border rounded">
              <div>
                <h3 className="font-medium">GitHub</h3>
                <p className="text-sm text-gray-500">
                  {githubStatus?.connected
                    ? `Connected to ${githubStatus.workspace}`
                    : 'Not connected'}
                </p>
              </div>
              <div className="flex gap-2">
                {githubStatus?.connected ? (
                  <>
                    <button
                      onClick={() => ingestMutation.mutate('github')}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Ingest
                    </button>
                    <button
                      onClick={() => disconnectMutation.mutate('github')}
                      className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Disconnect
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => connectMutation.mutate('github')}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Workflows */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Workflows</h2>
          <div className="grid grid-cols-2 gap-4">
            <button className="p-4 border rounded hover:bg-gray-50">
              <h3 className="font-medium">Daily Standup</h3>
              <p className="text-sm text-gray-500">View your daily tasks</p>
            </button>
            <button className="p-4 border rounded hover:bg-gray-50">
              <h3 className="font-medium">Process Messages</h3>
              <p className="text-sm text-gray-500">Create/update tickets</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

