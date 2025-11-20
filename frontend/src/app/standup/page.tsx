"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { loadSession } from "../../lib/auth";
import { getStandup, StandupData } from "../../lib/workflows";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function StandupPage() {
  const router = useRouter();

  useEffect(() => {
    const session = loadSession();
    if (!session) {
      router.replace("/login");
      return;
    }
  }, [router]);

  const { data: standup, isLoading, error, refetch } = useQuery<StandupData>({
    queryKey: ["standup"],
    queryFn: getStandup,
    retry: 1,
  });

  if (isLoading) {
    return (
      <div className="bg-slate-50 py-12">
        <div className="mx-auto max-w-6xl px-6">
          <div className="rounded-xl border border-slate-200 bg-white p-12 text-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent"></div>
            <p className="mt-4 text-sm text-slate-600">Loading standup data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-slate-50 py-12">
        <div className="mx-auto max-w-6xl px-6">
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <h2 className="text-lg font-semibold text-red-900">Error loading standup</h2>
            <p className="mt-2 text-sm text-red-700">
              {error instanceof Error ? error.message : "Failed to load standup data"}
            </p>
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => refetch()}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
              >
                Try again
              </button>
              <Link
                href="/dashboard"
                className="rounded-md border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100"
              >
                Back to dashboard
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!standup) {
    return null;
  }

  return (
    <div className="bg-slate-50 py-12">
      <div className="mx-auto max-w-6xl px-6">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Daily Standup</h1>
            <p className="mt-1 text-sm text-slate-500">
              {new Date().toLocaleDateString("en-US", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-slate-300 hover:bg-slate-50"
            >
              Refresh
            </button>
            <Link
              href="/dashboard"
              className="rounded-md border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-slate-300 hover:bg-slate-50"
            >
              Back to dashboard
            </Link>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="mb-8 grid gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-slate-500">In Progress</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {standup.in_progress.length}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-slate-500">Todo</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {standup.todo.length}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-slate-500">Backlog</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {standup.backlog.length}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-slate-500">Untracked Messages</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900">
              {standup.untracked_messages.length}
            </div>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* In Progress */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                🟢 In Progress ({standup.in_progress.length})
              </h2>
            </div>
            {standup.in_progress.length > 0 ? (
              <ul className="space-y-3">
                {standup.in_progress.map((ticket) => (
                  <li
                    key={ticket.identifier}
                    className="rounded-lg border border-slate-100 bg-slate-50 p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-slate-900">
                          {ticket.identifier}
                        </div>
                        <div className="mt-1 text-sm text-slate-600">{ticket.title}</div>
                      </div>
                      <span className="ml-3 rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-700">
                        {ticket.state}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No tickets in progress</p>
            )}
          </div>

          {/* Todo */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                🟡 Todo ({standup.todo.length})
              </h2>
            </div>
            {standup.todo.length > 0 ? (
              <ul className="space-y-3">
                {standup.todo.slice(0, 10).map((ticket) => (
                  <li
                    key={ticket.identifier}
                    className="rounded-lg border border-slate-100 bg-slate-50 p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-slate-900">
                          {ticket.identifier}
                        </div>
                        <div className="mt-1 text-sm text-slate-600">{ticket.title}</div>
                      </div>
                      <span className="ml-3 rounded-full bg-yellow-100 px-2.5 py-1 text-xs font-semibold text-yellow-700">
                        {ticket.state}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">No todo items</p>
            )}
            {standup.todo.length > 10 && (
              <p className="mt-4 text-xs text-slate-500">
                Showing 10 of {standup.todo.length} items
              </p>
            )}
          </div>
        </div>

        {/* Backlog */}
        <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              ⚪ Backlog ({standup.backlog.length})
            </h2>
          </div>
          {standup.backlog.length > 0 ? (
            <ul className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {standup.backlog.slice(0, 9).map((ticket) => (
                <li
                  key={ticket.identifier}
                  className="rounded-lg border border-slate-100 bg-slate-50 p-4"
                >
                  <div className="font-medium text-slate-900">{ticket.identifier}</div>
                  <div className="mt-1 text-sm text-slate-600 line-clamp-2">
                    {ticket.title}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">No backlog items</p>
          )}
          {standup.backlog.length > 9 && (
            <p className="mt-4 text-xs text-slate-500">
              Showing 9 of {standup.backlog.length} items
            </p>
          )}
        </div>

        {/* Untracked Messages */}
        {standup.untracked_messages.length > 0 && (
          <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-amber-900">
                ⚠️ Untracked Messages ({standup.untracked_messages.length})
              </h2>
              <span className="text-xs text-amber-700">
                {standup.tracked_messages} tracked, {standup.total_messages} total
              </span>
            </div>
            <p className="mb-4 text-sm text-amber-800">
              These Slack conversations don't reference any Linear tickets. Consider
              creating tickets or linking them to existing work.
            </p>
            <ul className="space-y-3">
              {standup.untracked_messages.map((msg, idx) => (
                <li
                  key={idx}
                  className="rounded-lg border border-amber-200 bg-white p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="font-medium text-slate-900">#{msg.channel}</span>
                        <span className="text-slate-500">•</span>
                        <span className="text-slate-600">{msg.user}</span>
                      </div>
                      <p className="mt-2 text-sm text-slate-700">{msg.text}...</p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Message Stats */}
        <div className="mt-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Message Activity</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <div className="text-sm font-medium text-slate-500">Total Messages</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900">
                {standup.total_messages}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-slate-500">Tracked</div>
              <div className="mt-1 text-2xl font-semibold text-green-600">
                {standup.tracked_messages}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-slate-500">Untracked</div>
              <div className="mt-1 text-2xl font-semibold text-amber-600">
                {standup.untracked_messages.length}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

