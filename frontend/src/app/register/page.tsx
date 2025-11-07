'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import axios from 'axios';
import { saveSession } from '../../lib/auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await axios.post(`${API_URL}/api/auth/register`, {
        email,
        password,
        full_name: fullName || undefined,
      });

      const loginPayload = new URLSearchParams();
      loginPayload.append('username', email);
      loginPayload.append('password', password);

      const loginResponse = await axios.post(
        `${API_URL}/api/auth/login`,
        loginPayload,
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );

      saveSession({
        token: loginResponse.data.access_token,
        tenantId: loginResponse.data.tenant_id,
        email,
      });

      router.push('/dashboard');
    } catch (err: any) {
      const message =
        err?.response?.data?.detail ?? 'We could not create your account. Try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[70vh] items-center justify-center bg-slate-50 px-6 py-16">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg shadow-slate-200/50">
        <h1 className="text-2xl font-semibold text-slate-900">Create your account</h1>
        <p className="mt-2 text-sm text-slate-500">
          Start your trial, connect your tools, and automate your PM workflows.
        </p>

        {error && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <div>
            <label htmlFor="name" className="text-sm font-medium text-slate-700">
              Full name <span className="text-slate-400">(optional)</span>
            </label>
            <input
              id="name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
              placeholder="Ada Lovelace"
            />
          </div>
          <div>
            <label htmlFor="email" className="text-sm font-medium text-slate-700">
              Work email
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
          <div>
            <label htmlFor="password" className="text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="mt-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm shadow-sm focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-200"
              placeholder="At least 8 characters"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-80"
          >
            {loading ? 'Creating account…' : 'Get started'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{' '}
          <Link href="/login" className="font-semibold text-brand-600 hover:text-brand-700">
            Log in
          </Link>
        </div>
      </div>
    </div>
  );
}

