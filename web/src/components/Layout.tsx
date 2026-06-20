import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../lib/auth";

const nav = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/events", label: "Events" },
  { to: "/connections", label: "Connections" },
];

const stages = [
  { key: "before_meet", label: "Before meet", desc: "Research · enrich · outreach" },
  { key: "meet", label: "Meet", desc: "Capture · score · route" },
  { key: "post_meet", label: "Post meet", desc: "Follow-up · CRM sync" },
];

export function Layout() {
  const { user, signOut } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r border-ink-700 bg-ink-800 p-5">
        <div className="mb-8 flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-warmth-warm/20 text-warmth-warm">
            ◐
          </div>
          <span className="text-lg font-semibold">Warmth</span>
        </div>

        <nav className="space-y-1">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm ${
                  isActive
                    ? "bg-ink-600 text-white"
                    : "text-gray-400 hover:bg-ink-700 hover:text-gray-200"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-8">
          <div className="px-3 text-xs uppercase tracking-wide text-gray-500">
            Lifecycle
          </div>
          <ol className="mt-2 space-y-2">
            {stages.map((s, i) => (
              <li key={s.key} className="rounded-lg bg-ink-900/60 px-3 py-2">
                <div className="text-sm text-gray-200">
                  {i + 1}. {s.label}
                </div>
                <div className="text-xs text-gray-500">{s.desc}</div>
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-8 rounded-lg border border-ink-600 px-3 py-2 text-xs text-gray-500">
          Capture on iPhone + Watch. Manage here.
        </div>

        <div className="mt-auto border-t border-ink-700 pt-4">
          <div className="flex items-center gap-3">
            {user?.photoURL ? (
              <img
                src={user.photoURL}
                alt={user.displayName ?? "User"}
                className="h-8 w-8 rounded-full"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink-600 text-sm">
                {(user?.displayName ?? user?.email ?? "?").charAt(0).toUpperCase()}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm text-gray-200">
                {user?.displayName ?? "Signed in"}
              </div>
              <div className="truncate text-xs text-gray-500">{user?.email}</div>
            </div>
          </div>
          <button
            onClick={() => signOut()}
            className="mt-3 w-full rounded-lg border border-ink-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-ink-700"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}
