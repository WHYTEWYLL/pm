'use client';

import Link from 'next/link';
import { FormEvent, useState } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus(null);
    setError(null);
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/forgot-password`, {
        email,
      });
      setStatus('If an account exists for this email, a reset link will be sent.');
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ?? 'Unable to process your request right now.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[70vh] items-center justify-center bg-slate-50 px-6 py-16">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg shadow-slate-200/50">
        <h1 className="text-2xl font-semibold text-slate-900">Forgot password</h1>
        <p className="mt-2 text-sm text-slate-500">
          Enter your email and we&apos;ll send instructions to reset your password.
        </p>

        {status && (
          <div className="mt-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
            {status}
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <div>
            <label htmlFor="email" className="text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
              placeholder="you@example.com"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-80"
          >
            {loading ? 'Sending…' : 'Send reset link'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-500">
          Remembered it?{' '}
          <Link href="/login" className="font-semibold text-brand-600 hover:text-brand-700">
            Go back to login
          </Link>
        </div>
      </div>
    </div>
  );
}

