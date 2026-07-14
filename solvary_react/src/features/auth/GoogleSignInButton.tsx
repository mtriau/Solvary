/**
 * "Sign in with Google" via Google Identity Services. Renders nothing unless
 * VITE_GOOGLE_CLIENT_ID is configured. GIS returns an ID token (credential);
 * the backend verifies it against Google's JWKS and issues our tokens.
 */

import { useEffect, useRef, useState } from 'react';
import { env } from '@/shared/lib/env';

const GIS_SRC = 'https://accounts.google.com/gsi/client';

interface GoogleAccounts {
  accounts: {
    id: {
      initialize: (config: {
        client_id: string;
        callback: (response: { credential: string }) => void;
      }) => void;
      renderButton: (parent: HTMLElement, options: Record<string, unknown>) => void;
    };
  };
}

declare global {
  interface Window {
    google?: GoogleAccounts;
  }
}

function loadGis(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts) return resolve();
    const existing = document.querySelector(`script[src="${GIS_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve());
      return;
    }
    const script = document.createElement('script');
    script.src = GIS_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Sign-In'));
    document.head.appendChild(script);
  });
}

interface Props {
  onCredential: (credential: string) => void;
}

export default function GoogleSignInButton({ onCredential }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);
  const callbackRef = useRef(onCredential);
  callbackRef.current = onCredential;

  useEffect(() => {
    if (!env.googleClientId || !containerRef.current) return;
    let cancelled = false;

    loadGis()
      .then(() => {
        if (cancelled || !window.google || !containerRef.current) return;
        window.google.accounts.id.initialize({
          client_id: env.googleClientId,
          callback: (response) => callbackRef.current(response.credential),
        });
        window.google.accounts.id.renderButton(containerRef.current, {
          theme: 'outline',
          size: 'large',
          width: 320,
        });
      })
      .catch(() => setFailed(true));

    return () => {
      cancelled = true;
    };
  }, []);

  if (!env.googleClientId) return null;
  if (failed) return null;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="flex items-center gap-3 w-full">
        <div className="flex-1 h-px bg-gray-200" />
        <span className="text-xs text-gray-400">or</span>
        <div className="flex-1 h-px bg-gray-200" />
      </div>
      <div ref={containerRef} />
    </div>
  );
}
