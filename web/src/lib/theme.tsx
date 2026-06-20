import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  type ReactNode,
} from "react";

export type Theme = "light";

const STORAGE_KEY = "warmth.theme";

interface ThemeContextValue {
  theme: Theme;
  /** Light-only app — kept for callers that still reference a theme toggle. */
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function applyLightTheme() {
  document.documentElement.classList.remove("dark");
  document.documentElement.style.colorScheme = "light";
  // Clear any previously persisted "dark" preference so it can't override.
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

// Apply before first paint to avoid a dark flash.
applyLightTheme();

export function ThemeProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    applyLightTheme();
  }, []);

  const value = useMemo(
    () => ({ theme: "light" as const, toggleTheme: () => {} }),
    [],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
