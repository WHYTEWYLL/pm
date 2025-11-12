"use client";

import axios from "axios";
import { loadSession } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface SubscriptionStatus {
  tier: string;
  status: string;
  subscription_id?: string;
  is_trial: boolean;
  trial_ends_at?: string;
  is_trial_active: boolean;
  trial_days_remaining?: number;
}

export async function getSubscriptionStatus(): Promise<SubscriptionStatus> {
  const session = loadSession();
  if (!session) {
    throw new Error("Not authenticated");
  }

  const response = await axios.get(`${API_URL}/stripe/subscription`, {
    headers: {
      Authorization: `Bearer ${session.token}`,
    },
  });

  return response.data;
}

export async function createCheckoutSession(priceId: string): Promise<string> {
  const session = loadSession();
  if (!session) {
    throw new Error("Not authenticated");
  }

  const response = await axios.post(
    `${API_URL}/stripe/create-checkout?price_id=${priceId}`,
    {},
    {
      headers: {
        Authorization: `Bearer ${session.token}`,
      },
    }
  );

  return response.data.checkout_url;
}

