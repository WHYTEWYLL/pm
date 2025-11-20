"use client";

import axios from "axios";
import { loadSession } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StandupData {
  in_progress: Array<{
    identifier: string;
    title: string;
    state: string;
  }>;
  todo: Array<{
    identifier: string;
    title: string;
    state: string;
  }>;
  backlog: Array<{
    identifier: string;
    title: string;
    state: string;
  }>;
  untracked_messages: Array<{
    channel: string;
    text: string;
    user: string;
  }>;
  tracked_messages: number;
  total_messages: number;
}

export async function getStandup(): Promise<StandupData> {
  const session = loadSession();
  if (!session) {
    throw new Error("Not authenticated");
  }

  const response = await axios.get(`${API_URL}/api/workflows/standup`, {
    headers: {
      Authorization: `Bearer ${session.token}`,
    },
  });

  return response.data;
}

