import { GlassCard } from "../components/Glass";
import { COMMUNITY_GROUPS, type PermissionLevel } from "../lib/mockData";

const PERMISSION_STYLES: Record<PermissionLevel, string> = {
  admin: "border-signal-intent/45 bg-signal-intent/15 text-signal-intent",
  edit: "border-signal-funding/45 bg-signal-funding/15 text-signal-funding",
  comment: "border-signal-hiring/45 bg-signal-hiring/15 text-signal-hiring",
  read: "border-subtle bg-muted text-ink-muted",
};

const ACTIONS: Record<PermissionLevel, string> = {
  admin: "Manage access",
  edit: "Share selected leads",
  comment: "Add comment",
  read: "Invite member",
};

export function Community() {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Community Sharing</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Share leads and conversation intel with your groups.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {COMMUNITY_GROUPS.map((group) => (
          <GlassCard key={group.id} className="p-5">
            <h3 className="text-base font-semibold text-ink-900">{group.name}</h3>
            <p className="mt-0.5 text-sm text-ink-muted">
              {group.members} members · {group.permission} access
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className={`glass-pill capitalize ${PERMISSION_STYLES[group.permission]}`}>
                {group.permission}
              </span>
              <span className="glass-pill border-orange/25 bg-orange/10 text-flame">
                {group.sharedLeads} shared leads
              </span>
            </div>
            <button type="button" className="btn-secondary mt-4 w-full py-2">
              {ACTIONS[group.permission]}
            </button>
          </GlassCard>
        ))}
      </div>
    </div>
  );
}
