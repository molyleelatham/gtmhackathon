import { createContext, useContext, useMemo, type ReactNode } from "react";

/** Demo auth — matches backend DEMO_USER_ID without Firebase for hackathon E2E. */
interface AuthUser {
  uid: string;
  email: string;
  displayName: string;
  photoURL?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const DEMO_USER: AuthUser = {
  uid: "demo-user",
  email: "getwarmth@gmail.com",
  displayName: "Warmth",
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const value = useMemo<AuthContextValue>(
    () => ({
      user: DEMO_USER,
      loading: false,
      signInWithGoogle: async () => {},
      signOut: async () => {},
    }),
    [],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
