import { Link } from "react-router-dom";
import { GlassCard } from "../components/Glass";
import { WarmthBadge } from "../components/WarmthBadge";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { ErrorBox, Loading } from "./Dashboard";

export function Leads() {
  const { data, error, loading, reload } = useAsync(() => api.listLeads(), []);

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink-900">CRM Leads</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Leads pushed to Zero CRM after meet routing and iOS capture signals.
          </p>
        </div>
        <button type="button" onClick={reload} className="btn-secondary">
          Refresh
        </button>
      </header>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {data?.map((lead) => (
          <GlassCard key={lead.id} className="p-5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h2 className="font-semibold text-ink-900">
                  {lead.contact_name ?? "Unknown contact"}
                </h2>
                <p className="text-sm text-ink-muted">{lead.company_name}</p>
              </div>
              <WarmthBadge score={lead.icp_score} />
            </div>
            <dl className="mt-4 space-y-1 text-xs text-ink-muted">
              {lead.contact_email && (
                <div>
                  <span className="text-ink-faint">Email · </span>
                  {lead.contact_email}
                </div>
              )}
              {lead.funding_stage && (
                <div>
                  <span className="text-ink-faint">Stage · </span>
                  {lead.funding_stage}
                </div>
              )}
              <div>
                <span className="text-ink-faint">Source · </span>
                {lead.signal_source.replace(/_/g, " ")}
              </div>
            </dl>
            {lead.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {lead.tags.map((tag) => (
                  <span
                    key={tag}
                    className="glass-pill border-orange/25 bg-orange/10 text-flame"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </GlassCard>
        ))}
      </div>

      {data && data.length === 0 && (
        <p className="text-sm text-ink-faint">
          No CRM leads yet — run a meet simulation or ingest an iOS signal from{" "}
          <Link to="/app/pipeline" className="text-flame hover:text-ember">
            Pipeline
          </Link>
          .
        </p>
      )}
    </div>
  );
}
