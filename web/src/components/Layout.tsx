import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Avatar } from "./Avatar";

const nav = [
  { to: "/app", label: "Dashboard", icon: "◫", end: true },
  { to: "/app/connections", label: "Connections", icon: "👥" },
  { to: "/app/leads", label: "CRM Leads", icon: "◆" },
  { to: "/app/events", label: "Events", icon: "📅" },
  { to: "/app/pipeline", label: "Pipeline", icon: "⚡" },
  { to: "/app/community", label: "Community", icon: "◎" },
];

export function Layout() {
  const { user } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const health = useAsync(() => api.health(), []);

  const apiOk = health.data?.status === "healthy";

  return (
    <div className="flex min-h-screen gap-3 p-3">
      <aside
        className={`glass-strong flex shrink-0 flex-col p-3 transition-all duration-300 ${
          collapsed ? "w-[4.5rem]" : "w-64"
        }`}
      >
        <div className={`mb-6 flex items-center ${collapsed ? "justify-center" : "gap-3 px-1"}`}>
          {!collapsed && (
            <Avatar
              name={user?.displayName ?? "User"}
              photoURL={user?.photoURL}
              size="sm"
            />
          )}
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-ink-900">
                {user?.displayName ?? "Signed in"}
              </p>
              <p className="flex items-center gap-1.5 text-xs text-ink-faint">
                <span
                  className={`inline-block h-1.5 w-1.5 rounded-full ${
                    apiOk ? "bg-warmth-warm" : health.loading ? "bg-amber" : "bg-red-brand"
                  }`}
                  title={apiOk ? "API healthy" : "API unreachable"}
                />
                {apiOk
                  ? health.data?.listener_running
                    ? "Listener active"
                    : "API online"
                  : health.loading
                    ? "Checking API…"
                    : "API offline"}
              </p>
            </div>
          )}
          <button
            onClick={() => setCollapsed((c) => !c)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="icon-btn h-8 w-8 shrink-0"
          >
            {collapsed ? "→" : "←"}
          </button>
        </div>

        <nav className="space-y-1">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              title={collapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center rounded-xl py-2.5 text-sm transition-all ${
                  collapsed ? "justify-center px-2" : "gap-3 px-3"
                } ${
                  isActive
                    ? "border border-orange/30 bg-orange/10 font-semibold text-flame"
                    : "border border-transparent text-ink-muted hover:bg-[var(--hover-overlay)] hover:text-ink-900"
                }`
              }
            >
              <span className="w-5 shrink-0 text-center">{item.icon}</span>
              {!collapsed && item.label}
            </NavLink>
          ))}
        </nav>

        {!collapsed && (
          <div className="mt-6 rounded-xl border border-subtle bg-orange/5 px-3 py-2.5 text-xs text-ink-muted">
            Capture on iPhone &amp; Apple Watch. Manage the full lifecycle here.
          </div>
        )}

        <div className="mt-auto space-y-1 pt-4">
          <NavLink
            to="/app/settings"
            title={collapsed ? "Settings" : undefined}
            className={({ isActive }) =>
              `flex items-center rounded-xl py-2.5 text-sm transition-all ${
                collapsed ? "justify-center px-2" : "gap-3 px-3"
              } ${
                isActive
                  ? "border border-orange/30 bg-orange/10 font-semibold text-flame"
                  : "border border-subtle text-ink-muted hover:bg-[var(--hover-overlay)]"
              }`
            }
          >
            <span className="w-5 shrink-0 text-center">⚙</span>
            {!collapsed && "Settings"}
          </NavLink>
        </div>
      </aside>

      <main className="min-w-0 flex-1 overflow-y-auto rounded-2xl">
        <div className="animate-fade-up p-5">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
