import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { auth, googleSignInProvider } from "./firebase";
import { api, setAuthTokenGetter } from "./api";

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
  getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const E2E_BYPASS_AUTH =
  import.meta.env.VITE_E2E_BYPASS_AUTH === "true" ||
  (typeof window !== "undefined" && localStorage.getItem("warmth_e2e_auth") === "1");

const E2E_USER: AuthUser = {
  uid: "e2e-test-user",
  displayName: "E2E Test User",
  email: "e2e@warmth.test",
  photoURL: null,
};

function mapFirebaseUser(user: User): AuthUser {
  return {
    uid: user.uid,
    displayName: user.displayName,
    email: user.email,
    photoURL: user.photoURL,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(E2E_BYPASS_AUTH ? E2E_USER : null);
  const [loading, setLoading] = useState(!E2E_BYPASS_AUTH);
  const bootstrapStarted = useRef<string | null>(null);

  const getIdToken = useCallback(async (): Promise<string | null> => {
    const current = auth.currentUser;
    if (!current) return null;
    try {
      return await current.getIdToken();
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (E2E_BYPASS_AUTH) {
      setAuthTokenGetter(async () => "e2e-test-token");
      return () => setAuthTokenGetter(null);
    }
    setAuthTokenGetter(getIdToken);
    return () => setAuthTokenGetter(null);
  }, [getIdToken]);

  useEffect(() => {
    if (E2E_BYPASS_AUTH) return;

    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      if (!firebaseUser) {
        bootstrapStarted.current = null;
        setUser(null);
        setLoading(false);
        return;
      }

      const mapped = mapFirebaseUser(firebaseUser);
      setUser(mapped);
      setLoading(false);

      if (bootstrapStarted.current !== mapped.uid) {
        bootstrapStarted.current = mapped.uid;
        void api.bootstrapProfile().catch(() => {
          /* best-effort; profile sync can retry on next navigation */
        });
      }
    });

    return unsubscribe;
  }, []);

  const signInWithGoogle = useCallback(async () => {
    const result = await signInWithPopup(auth, googleSignInProvider());
    setUser(mapFirebaseUser(result.user));
  }, []);

  const signOut = useCallback(async () => {
    bootstrapStarted.current = null;
    await firebaseSignOut(auth);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signInWithGoogle, signOut, getIdToken }),
    [user, loading, signInWithGoogle, signOut, getIdToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
