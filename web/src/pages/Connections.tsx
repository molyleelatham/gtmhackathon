import { Link } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { CompanyLogo } from "../components/CompanyLogo";
import { ConnectionWeb } from "../components/ConnectionWeb";
import { WarmthBadge } from "../components/WarmthBadge";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";

export function Connections() {
  const { data, error, loading } = useAsync(() => api.listConnections(), []);

  const sorted = [...(data ?? [])].sort(
    (a, b) => b.predicted_warmth - a.predicted_warmth,
  );

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Connections</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Everyone Warmth has identified or met, scored by warmth.
        </p>
      </header>

      <ConnectionWeb />

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((c) => (
          <Link
            key={c.id}
            to={`/connections/${c.id}`}
            className="glass glass-interactive p-4"
          >
            <div className="flex items-start gap-3">
              <Avatar name={c.name ?? "Unknown"} size="md" />
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-semibold text-ink-900">{c.name ?? "Unknown"}</div>
                    <div className="mt-0.5 flex items-center gap-2">
                      <CompanyLogo company={c.company_name ?? ""} size="sm" />
                      <span className="text-xs text-ink-muted">{c.title ?? ""}</span>
                    </div>
                  </div>
                  <WarmthBadge score={c.predicted_warmth} />
                </div>
                <div className="mt-2 text-sm text-ink-muted">{c.company_name ?? "—"}</div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {c.interests.slice(0, 3).map((i) => (
                    <span
                      key={i}
                      className="glass-pill border-orange/25 bg-orange/10 text-flame"
                    >
                      {i}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
      {data && data.length === 0 && (
        <p className="text-sm text-ink-faint">No connections yet.</p>
      )}
    </div>
  );
}
