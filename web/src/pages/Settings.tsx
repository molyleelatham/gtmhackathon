import { GlassCard } from "../components/Glass";
import { useAuth } from "../lib/auth";
import { ICP_PROFILE, INTEGRATIONS, type Integration } from "../lib/mockData";

const DOT: Record<Integration["status"], string> = {
  connected: "bg-warmth-warm",
  pending: "bg-amber",
  offline: "bg-signal-intent",
};

export function Settings() {
  const { user, signOut } = useAuth();
  const initial = (user?.displayName ?? "?").charAt(0).toUpperCase();

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Settings</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Account, ideal customer profile, and connected services.
        </p>
      </header>

      <GlassCard className="flex items-center justify-between gap-4 p-5">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-orange to-ember text-lg font-bold text-white shadow-glass">
            {initial}
          </div>
          <div>
            <div className="font-semibold text-ink-900">{user?.displayName ?? "Signed in"}</div>
            <div className="text-sm text-ink-muted">{user?.email}</div>
          </div>
        </div>
        <button
          onClick={() => signOut()}
          className="glass-interactive rounded-xl border border-black/10 bg-white px-4 py-2 text-sm font-medium text-ink-800"
        >
          Sign out
        </button>
      </GlassCard>

      <div className="grid gap-4 lg:grid-cols-2">
        <GlassCard className="p-5">
          <h3 className="text-base font-semibold text-ink-900">Ideal Customer Profile</h3>
          <dl className="mt-3">
            {ICP_PROFILE.map((row) => (
              <div
                key={row.label}
                className="flex items-center justify-between gap-4 border-b border-black/[0.06] py-2.5 text-sm last:border-0"
              >
                <dt className="text-ink-muted">{row.label}</dt>
                <dd className="text-right font-medium text-ink-900">{row.value}</dd>
              </div>
            ))}
          </dl>
          <button className="glass-interactive mt-4 rounded-xl border border-black/10 bg-white px-4 py-2 text-sm font-medium text-ink-800">
            Edit ICP
          </button>
        </GlassCard>

        <GlassCard className="p-5">
          <h3 className="text-base font-semibold text-ink-900">Integrations</h3>
          <ul className="mt-3">
            {INTEGRATIONS.map((item) => (
              <li
                key={item.name}
                className="flex items-center justify-between border-b border-black/[0.06] py-2.5 text-sm last:border-0"
              >
                <span className="flex items-center gap-2.5 text-ink-900">
                  <span className={`h-2 w-2 rounded-full ${DOT[item.status]}`} />
                  {item.name}
                </span>
                <span className="capitalize text-ink-faint">{item.status}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
    </div>
  );
}
