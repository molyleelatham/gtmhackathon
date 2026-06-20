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

const DEMO_USER: AuthUser = {
  uid: "demo-user",
  displayName: "Nicholas Wong",
  email: "nicholas@warmth.ai",
  photoURL: null,
};

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Lightweight demo auth provider — no Firebase/network required so the first
 * draft runs anywhere. The session persists in localStorage. Swap the body of
 * `signInWithGoogle`/`signOut` for Firebase Auth (`signInWithPopup`) when the
 * backend is wired up; the consumer API stays identical.
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
