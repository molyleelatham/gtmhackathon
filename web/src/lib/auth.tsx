import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface AuthUser {
  uid: string;
  displayName: string | null;
  email: string | null;
  photoURL: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const STORAGE_KEY = "warmth.demo.user";

/** Matches backend DEMO_USER_ID (`apps/api/store.py`). */
const DEMO_USER: AuthUser = {
  uid: "demo-user",
  displayName: "Nicholas Wong",
  email: "nicholas@warmth.ai",
  photoURL: null,
};

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Demo auth with localStorage persistence — no Firebase required for hackathon E2E.
 * Swap signInWithGoogle/signOut for Firebase Auth when production auth is wired.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setUser(JSON.parse(stored) as AuthUser);
    } catch {
      /* ignore corrupt storage */
    }
    setLoading(false);
  }, []);

  const signInWithGoogle = useCallback(async () => {
    await new Promise((r) => setTimeout(r, 300));
    setUser(DEMO_USER);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEMO_USER));
    } catch {
      /* ignore */
    }
  }, []);

  const signOut = useCallback(async () => {
    setUser(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, signInWithGoogle, signOut }),
    [user, loading, signInWithGoogle, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
