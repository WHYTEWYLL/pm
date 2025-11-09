'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

type Status = 'loading' | 'success' | 'error';

export default function OAuthCallbackPage() {
  const { service } = useParams<{ service: string }>();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<Status>('loading');
  const [message, setMessage] = useState('Finishing authorization…');

  const params = useMemo(() => {
    return {
      code: searchParams.get('code'),
      state: searchParams.get('state'),
      error: searchParams.get('error'),
      errorDescription: searchParams.get('error_description'),
    };
  }, [searchParams]);

  useEffect(() => {
    const notifyAndMaybeClose = (success: boolean, error?: string) => {
      if (window.opener) {
        window.opener.postMessage(
          {
            type: 'oauth-complete',
            service,
            success,
            error,
          },
          window.location.origin,
        );
      }

      setTimeout(() => {
        if (window.opener) {
          window.close();
        }
      }, 1500);
    };

    if (!service || typeof service !== 'string') {
      setStatus('error');
      setMessage('Missing service in callback URL.');
      notifyAndMaybeClose(false, 'Missing service parameter.');
      return;
    }

    if (params.error) {
      setStatus('error');
      setMessage(`Authorization failed: ${params.errorDescription ?? params.error}`);
      notifyAndMaybeClose(false, params.errorDescription ?? params.error);
      return;
    }

    if (!params.code || !params.state) {
      setStatus('error');
      setMessage('Authorization code or state was not provided.');
      notifyAndMaybeClose(false, 'Missing code/state.');
      return;
    }

    const finalize = async () => {
      try {
        await axios.get(`${API_URL}/api/oauth/${service}/callback`, {
          params: {
            code: params.code,
            state: params.state,
          },
        });
        setStatus('success');
        setMessage('Integration connected successfully. You can close this window.');
        notifyAndMaybeClose(true);
      } catch (err: any) {
        const detail =
          err?.response?.data?.detail ??
          err?.message ??
          'Unexpected error while completing authorization.';
        setStatus('error');
        setMessage(detail);
        notifyAndMaybeClose(false, detail);
      }
    };

    finalize();
  }, [service, params]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg shadow-slate-200/50">
        <h1 className="text-xl font-semibold text-slate-900">Authorization Status</h1>
        <p className="mt-3 text-sm text-slate-600">{message}</p>
        {status === 'loading' && (
          <p className="mt-4 text-xs text-slate-400">
            Please keep this window open while we finish connecting your account.
          </p>
        )}
        {status === 'success' && (
          <p className="mt-4 text-xs text-green-600">
            This window will close automatically in a moment. You can return to the dashboard.
          </p>
        )}
        {status === 'error' && (
          <p className="mt-4 text-xs text-red-600">
            You may close this window and try again. If the issue persists, contact support.
          </p>
        )}
      </div>
    </div>
  );
}

