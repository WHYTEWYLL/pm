'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import Link from 'next/link';
import { 
  ArrowLeft,
  RefreshCw,
  Link2,
  GitPullRequest,
  FileText,
  Send,
  ChevronDown,
  Loader2
} from 'lucide-react';
import { loadSession, AuthSession } from '../../../lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type ActivityType = 'sync' | 'link' | 'move' | 'create' | 'post';

interface ActivityItem {
  id: string;
  type: ActivityType;
  description: string;
  metadata?: {
    ticket_id?: string;
    ticket_title?: string;
    channel?: string;
    count?: number;
  };
  created_at: string;
}

interface ActivityResponse {
  items: ActivityItem[];
  metrics: { synced: number; linked: number; moved: number; created: number };
  has_more: boolean;
}

export default function ActivityPage() {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | 'all'>('7d');

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
    return { Authorization: `Bearer ${session.token}` };
  }, [session]);

  const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 365;

  const activityQuery = useQuery<ActivityResponse>({
    queryKey: ['activity', timeRange],
    queryFn: async () => (await axios.get(`${API_URL}/api/settings/activity?days=${days}&limit=50`, { headers: authHeaders })).data,
    enabled: !!authHeaders,
  });

  const activities = activityQuery.data?.items ?? [];
  const isLoading = activityQuery.isLoading;

  if (!session) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-50 to-slate-100">
      <main className="mx-auto max-w-4xl px-6 py-10">
        {/* Page Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link 
              href="/dashboard"
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
            >
              <ArrowLeft size={20} />
            </Link>
            <h1 className="text-xl font-semibold text-slate-900">Activity Log</h1>
          </div>
          <div className="relative">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as '7d' | '30d' | 'all')}
              className="appearance-none rounded-lg border border-slate-200 bg-white py-2 pl-4 pr-10 text-sm font-medium text-slate-700 shadow-sm hover:border-slate-300 focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500/20"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="all">All time</option>
            </select>
            <ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
          </div>
        </div>
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 size={24} className="animate-spin text-violet-600" />
              <span className="ml-3 text-sm text-slate-500">Loading activity...</span>
            </div>
          ) : activities.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-slate-500">No activity yet.</p>
              <p className="mt-1 text-sm text-slate-400">Workflows will log their actions here.</p>
            </div>
          ) : (
            <>
              <div className="divide-y divide-slate-100">
                {activities.map((activity) => (
                  <ActivityRow key={activity.id} activity={activity} />
                ))}
              </div>
              
              {/* Load More */}
              {activityQuery.data?.has_more && (
                <div className="border-t border-slate-100 px-6 py-4 text-center">
                  <button className="text-sm font-medium text-violet-600 hover:text-violet-700 hover:underline">
                    Load more
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function ActivityRow({ activity }: { activity: ActivityItem }) {
  const iconMap: Record<ActivityType, React.ReactNode> = {
    sync: <RefreshCw size={16} />,
    link: <Link2 size={16} />,
    move: <GitPullRequest size={16} />,
    create: <FileText size={16} />,
    post: <Send size={16} />,
  };

  const colorMap: Record<ActivityType, string> = {
    sync: 'bg-slate-100 text-slate-600',
    link: 'bg-violet-100 text-violet-600',
    move: 'bg-amber-100 text-amber-600',
    create: 'bg-emerald-100 text-emerald-600',
    post: 'bg-blue-100 text-blue-600',
  };

  const emojiMap: Record<ActivityType, string> = {
    sync: '📥',
    link: '🔗',
    move: '→',
    create: '📝',
    post: '📤',
  };

  return (
    <div className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-slate-50">
      <div className={`rounded-lg p-2 ${colorMap[activity.type]}`}>
        {iconMap[activity.type]}
      </div>
      <div className="flex-1">
        <p className="text-sm text-slate-900">
          <span className="mr-2">{emojiMap[activity.type]}</span>
          {activity.description}
        </p>
      </div>
      <span className="text-xs text-slate-400">
        {formatTimeAgo(activity.created_at)}
      </span>
    </div>
  );
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) {
    return 'Just now';
  } else if (diffHours < 24) {
    return `${diffHours}h ago`;
  } else if (diffDays === 1) {
    return '1d ago';
  } else {
    return `${diffDays}d ago`;
  }
}

