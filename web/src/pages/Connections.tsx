import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";
import { WarmthBadge } from "../components/WarmthBadge";

export function Connections() {
  const { data, error, loading } = useAsync(() => api.listConnections(), []);

  const sorted = [...(data ?? [])].sort(
    (a, b) => b.predicted_warmth - a.predicted_warmth,
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Connections</h1>
        <p className="text-sm text-gray-400">
          Everyone Warmth has identified or met, scored by warmth.
        </p>
      </header>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {sorted.map((c) => (
          <Link
            key={c.id}
            to={`/connections/${c.id}`}
            className="rounded-xl border border-ink-600 bg-ink-800 p-4 transition hover:border-warmth-warm/50"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium">{c.name ?? "Unknown"}</div>
                <div className="text-xs text-gray-500">{c.title ?? ""}</div>
              </div>
              <WarmthBadge score={c.predicted_warmth} />
            </div>
            <div className="mt-3 text-sm text-gray-400">{c.company_name ?? "—"}</div>
            <div className="mt-2 flex flex-wrap gap-1">
              {c.interests.slice(0, 3).map((i) => (
                <span
                  key={i}
                  className="rounded-full bg-ink-700 px-2 py-0.5 text-xs text-gray-300"
                >
                  {i}
                </span>
              ))}
            </div>
          </Link>
        ))}
      </div>
      {data && data.length === 0 && (
        <p className="text-sm text-gray-500">No connections yet.</p>
      )}
    </div>
  );
}
