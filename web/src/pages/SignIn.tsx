import { useState } from "react";
import { useAuth } from "../lib/auth";

export function SignIn() {
  const { signInWithGoogle } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSignIn() {
    setBusy(true);
    setError(null);
    try {
      await signInWithGoogle();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-2xl border border-ink-600 bg-ink-800 p-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-warmth-warm/20 text-2xl text-warmth-warm">
          ◐
        </div>
        <h1 className="text-xl font-semibold">Warmth</h1>
        <p className="mt-1 text-sm text-gray-400">
          Your personal CRM for conference connections.
        </p>

        <button
          onClick={handleSignIn}
          disabled={busy}
          className="mt-6 flex w-full items-center justify-center gap-3 rounded-lg bg-white px-4 py-2.5 text-sm font-medium text-gray-800 transition hover:bg-gray-100 disabled:opacity-60"
        >
          <GoogleIcon />
          {busy ? "Signing in…" : "Continue with Google"}
        </button>

        {error && (
          <p className="mt-4 rounded-lg border border-warmth-hot/40 bg-warmth-hot/10 p-3 text-xs text-warmth-hot">
            {error}
          </p>
        )}

        <p className="mt-6 text-xs text-gray-500">
          Capture connections on iPhone &amp; Apple Watch. Manage them here.
        </p>
      </div>
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.85.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.96v2.33A9 9 0 0 0 9 18z"
      />
      <path
        fill="#FBBC05"
        d="M3.97 10.72a5.41 5.41 0 0 1 0-3.44V4.95H.96a9 9 0 0 0 0 8.1l3.01-2.33z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58A9 9 0 0 0 9 0 9 9 0 0 0 .96 4.95l3.01 2.33C4.68 5.16 6.66 3.58 9 3.58z"
      />
    </svg>
  );
}
