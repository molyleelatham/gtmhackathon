import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Avatar } from "../components/Avatar";
import { CompanyLogo } from "../components/CompanyLogo";
import { WarmthBadge } from "../components/WarmthBadge";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { Loading, ErrorBox } from "./Dashboard";

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`glass-pill transition-colors ${
        active
          ? "border-orange/40 bg-orange/15 text-flame"
          : "border-subtle bg-glass-strong text-ink-muted hover:text-ink-900"
      }`}
    >
      {children}
    </button>
  );
}

function FilterRow({
  label,
  options,
  selected,
  onSelect,
}: {
  label: string;
  options: string[];
  selected: string | null;
  onSelect: (value: string | null) => void;
}) {
  if (options.length === 0) return null;

  return (
    <div className="space-y-2">
      <span className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
        {label}
      </span>
      <div className="flex flex-wrap gap-1.5">
        <FilterChip active={selected === null} onClick={() => onSelect(null)}>
          All
        </FilterChip>
        {options.map((opt) => (
          <FilterChip key={opt} active={selected === opt} onClick={() => onSelect(opt)}>
            {opt}
          </FilterChip>
        ))}
      </div>
    </div>
  );
}

export function Connections() {
  const { data, error, loading } = useAsync(() => api.listConnections(), []);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [interest, setInterest] = useState<string | null>(null);
  const [industry, setIndustry] = useState<string | null>(null);
  const [funding, setFunding] = useState<string | null>(null);

  const filterOptions = useMemo(() => {
    const connections = data ?? [];
    return {
      interests: [...new Set(connections.flatMap((c) => c.interests))].sort(),
      industries: [
        ...new Set(
          connections.map((c) => c.industry).filter((v): v is string => Boolean(v)),
        ),
      ].sort(),
      funding: [
        ...new Set(
          connections.map((c) => c.funding_stage).filter((v): v is string => Boolean(v)),
        ),
      ].sort(),
    };
  }, [data]);

  const filtered = useMemo(() => {
    let list = [...(data ?? [])];
    if (interest) list = list.filter((c) => c.interests.includes(interest));
    if (industry) list = list.filter((c) => c.industry === industry);
    if (funding) list = list.filter((c) => c.funding_stage === funding);
    return list.sort((a, b) => b.predicted_warmth - a.predicted_warmth);
  }, [data, interest, industry, funding]);

  const hasFilters = interest !== null || industry !== null || funding !== null;
  const activeFilterCount = [interest, industry, funding].filter(Boolean).length;

  function clearFilters() {
    setInterest(null);
    setIndustry(null);
    setFunding(null);
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight text-ink-900">Connections</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Everyone Warmth has identified or met, scored by warmth.
        </p>
      </header>

      {loading && <Loading />}
      {error && <ErrorBox message={error} />}

      {data && data.length > 0 && (
        <section className="glass overflow-hidden">
          <button
            type="button"
            onClick={() => setFiltersOpen((open) => !open)}
            aria-expanded={filtersOpen}
            className="glass-interactive flex w-full items-center justify-between gap-2 p-4 text-left"
          >
            <span className="text-sm font-semibold text-ink-900">
              Filter connections
              {activeFilterCount > 0 && (
                <span className="text-flame"> ({activeFilterCount})</span>
              )}
            </span>
            <svg
              aria-hidden
              viewBox="0 0 20 20"
              fill="currentColor"
              className={`h-4 w-4 shrink-0 text-ink-muted transition-transform duration-200 ${
                filtersOpen ? "rotate-180" : ""
              }`}
            >
              <path
                fillRule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                clipRule="evenodd"
              />
            </svg>
          </button>

          {filtersOpen && (
            <div className="space-y-4 border-t border-subtle p-4">
              {hasFilters && (
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="text-xs font-semibold text-flame hover:text-ember"
                  >
                    Reset all
                  </button>
                </div>
              )}
              <FilterRow
                label="Interests"
                options={filterOptions.interests}
                selected={interest}
                onSelect={setInterest}
              />
              <FilterRow
                label="Industry"
                options={filterOptions.industries}
                selected={industry}
                onSelect={setIndustry}
              />
              <FilterRow
                label="Funding stage"
                options={filterOptions.funding}
                selected={funding}
                onSelect={setFunding}
              />
            </div>
          )}
        </section>
      )}

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((c) => (
          <Link key={c.id} to={`/connections/${c.id}`} className="person-card">
            <WarmthBadge score={c.predicted_warmth} className="person-card-badge" />
            <div className="person-card-body">
              <Avatar name={c.name ?? "Unknown"} size="md" />
              <div className="person-card-info">
                <p className="truncate font-semibold text-ink-900">{c.name ?? "Unknown"}</p>
                <div className="mt-0.5 flex items-center gap-2">
                  <CompanyLogo company={c.company_name ?? ""} size="sm" />
                  <span className="truncate text-xs text-ink-muted">{c.title ?? ""}</span>
                </div>
                <p className="mt-1 truncate text-sm text-ink-muted">{c.company_name ?? "—"}</p>
                {c.interests.length > 0 && (
                  <div className="person-card-pills">
                    {c.interests.slice(0, 3).map((i) => (
                      <span key={i} className="person-card-pill">
                        {i}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {data && data.length === 0 && (
        <p className="text-sm text-ink-faint">No connections yet.</p>
      )}
      {data && data.length > 0 && filtered.length === 0 && (
        <p className="text-sm text-ink-faint">No connections match the selected filters.</p>
      )}
    </div>
  );
}
