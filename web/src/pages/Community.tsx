import { Avatar } from "../components/Avatar";
import { GlassCard } from "../components/Glass";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { ErrorBox, Loading } from "./Dashboard";
import { Acronym } from "../components/Acronym";

export function Community() {
  const members = useAsync(() => api.communityMembers(), []);
  const dashboard = useAsync(() => api.dashboard(), []);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Community Sharing</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Share leads and conversation intel with your founder network.
        </p>
      </header>

      {(members.error || dashboard.error) && (
        <ErrorBox message={members.error ?? dashboard.error ?? ""} />
      )}
      {(members.loading || dashboard.loading) && <Loading />}

      {members.data && (
        <>
          <GlassCard className="p-5">
            <h3 className="text-base font-semibold text-ink-900">Founder Community</h3>
            <p className="mt-1 text-sm text-ink-muted">
              {members.data.length} members · {dashboard.data?.leads_in_crm ?? 0} leads in{" "}
              <Acronym term="CRM">CRM</Acronym>
            </p>
          </GlassCard>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {members.data.map((member) => (
              <GlassCard key={member.user_id} className="p-5">
                <div className="flex items-center gap-3">
                  <Avatar name={member.name} size="md" />
                  <div>
                    <h3 className="font-semibold text-ink-900">{member.name}</h3>
                    <p className="text-xs text-ink-faint">{member.user_id.replace(/_/g, " ")}</p>
                  </div>
                </div>
                {member.interests.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1.5">
                    {member.interests.map((interest) => (
                      <span
                        key={interest}
                        className="glass-pill border-orange/25 bg-orange/10 text-flame"
                      >
                        {interest}
                      </span>
                    ))}
                  </div>
                )}
                <button type="button" className="btn-secondary mt-4 w-full py-2">
                  Share selected leads
                </button>
              </GlassCard>
            ))}
          </div>

          {members.data.length === 0 && (
            <p className="text-sm text-ink-faint">No community members configured yet.</p>
          )}
        </>
      )}
    </div>
  );
}
