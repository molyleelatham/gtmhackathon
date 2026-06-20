import { useState } from "react";
import { GlassCard } from "../components/Glass";
import { Toggle } from "../components/Toggle";
import { useAuth } from "../lib/auth";
import { ICP_PROFILE, INTEGRATIONS, type Integration } from "../lib/mockData";

const DOT: Record<Integration["status"], string> = {
  connected: "bg-warmth-warm",
  pending: "bg-amber",
  offline: "bg-signal-intent",
};

const STATUS_LABEL: Record<Integration["status"], string> = {
  connected: "Connected",
  pending: "Pending",
  offline: "Offline",
};

function SettingsRow({
  label,
  value,
  children,
}: {
  label: string;
  value?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-subtle py-2.5 text-sm last:border-0">
      <span className="text-ink-muted">{label}</span>
      {children ?? <span className="text-right font-medium text-ink-900">{value}</span>}
    </div>
  );
}

function SectionHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-3">
      <h3 className="text-base font-semibold text-ink-900">{title}</h3>
      {description && <p className="mt-0.5 text-xs text-ink-faint">{description}</p>}
    </div>
  );
}

export function Settings() {
  const { user, signOut } = useAuth();
  const initial = (user?.displayName ?? "?").charAt(0).toUpperCase();

  const [emailAlerts, setEmailAlerts] = useState(true);
  const [pushAlerts, setPushAlerts] = useState(true);
  const [weeklyDigest, setWeeklyDigest] = useState(false);
  const [signalFeed, setSignalFeed] = useState(true);

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Settings</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Account, integrations, appearance, and preferences.
        </p>
      </header>

      {/* Account */}
      <GlassCard className="p-5">
        <SectionHeader title="Account" description="Your Warmth profile and session." />
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-orange to-ember text-lg font-bold text-white shadow-glass">
              {initial}
            </div>
            <div>
              <div className="font-semibold text-ink-900">{user?.displayName ?? "Signed in"}</div>
              <div className="text-sm text-ink-muted">{user?.email}</div>
            </div>
          </div>
          <button type="button" onClick={() => signOut()} className="btn-secondary">
            Sign out
          </button>
        </div>
      </GlassCard>


      <div className="grid gap-4 lg:grid-cols-2">
        {/* ICP Profile */}
        <GlassCard className="p-5">
          <SectionHeader
            title="Ideal Customer Profile"
            description="How Warmth scores attendee fit."
          />
          <dl>
            {ICP_PROFILE.map((row) => (
              <SettingsRow key={row.label} label={row.label} value={row.value} />
            ))}
          </dl>
          <button type="button" className="btn-secondary mt-4">
            Edit ICP
          </button>
        </GlassCard>

        {/* Integrations */}
        <GlassCard className="p-5">
          <SectionHeader title="Integrations" description="Connected services and sync status." />
          <ul>
            {INTEGRATIONS.map((item) => (
              <li
                key={item.name}
                className="flex items-center justify-between border-b border-subtle py-2.5 text-sm last:border-0"
              >
                <span className="flex items-center gap-2.5 text-ink-900">
                  <span className={`h-2 w-2 rounded-full ${DOT[item.status]}`} />
                  {item.name}
                </span>
                <span className="text-ink-faint">{STATUS_LABEL[item.status]}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>

      {/* Notifications */}
      <GlassCard className="p-5">
        <SectionHeader
          title="Notifications"
          description="Choose how Warmth keeps you in the loop."
        />
        <SettingsRow label="Email alerts for hot leads">
          <Toggle checked={emailAlerts} onChange={setEmailAlerts} accent />
        </SettingsRow>
        <SettingsRow label="Push notifications (iPhone & Watch)">
          <Toggle checked={pushAlerts} onChange={setPushAlerts} />
        </SettingsRow>
        <SettingsRow label="Weekly digest">
          <Toggle checked={weeklyDigest} onChange={setWeeklyDigest} />
        </SettingsRow>
        <SettingsRow label="Background signal feed">
          <Toggle checked={signalFeed} onChange={setSignalFeed} accent />
        </SettingsRow>
      </GlassCard>

      {/* Data & Privacy */}
      <GlassCard className="p-5">
        <SectionHeader
          title="Data & privacy"
          description="Your conversation data stays under your control."
        />
        <SettingsRow label="Data retention" value="90 days" />
        <SettingsRow label="Export my data">
          <button type="button" className="text-sm font-medium text-flame hover:text-ember">
            Request export
          </button>
        </SettingsRow>
        <SettingsRow label="Delete account">
          <button type="button" className="text-sm font-medium text-red-brand hover:text-red-warm">
            Contact support
          </button>
        </SettingsRow>
      </GlassCard>

      {/* About */}
      <GlassCard className="p-5">
        <SectionHeader title="About Warmth" />
        <p className="text-sm leading-relaxed text-ink-muted">
          Warmth is your personal CRM for conference connections — capture on iPhone &amp; Apple
          Watch, score by ICP fit, and follow up with AI-drafted outreach.
        </p>
        <dl className="mt-4">
          <SettingsRow label="Version" value="0.1.0 (hackathon)" />
          <SettingsRow label="Built for" value="GTM Hackathon 2026" />
        </dl>
      </GlassCard>
    </div>
  );
}
