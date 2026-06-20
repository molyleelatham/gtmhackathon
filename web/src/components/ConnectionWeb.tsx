import { useMemo } from "react";
import { Avatar } from "./Avatar";
import { ATTENDEES } from "../lib/mockData";

interface Node {
  id: string;
  name: string;
  interests: string[];
  x: number;
  y: number;
}

interface Edge {
  from: string;
  to: string;
  strength: number; // 0–1 shared-interest overlap
}

function overlap(a: string[], b: string[]): number {
  const setB = new Set(b.map((s) => s.toLowerCase()));
  const shared = a.filter((i) => setB.has(i.toLowerCase())).length;
  if (shared === 0) return 0;
  return shared / Math.max(a.length, b.length, 1);
}

/** Spider-web of mutual interests — warmer red = stronger connection. */
export function ConnectionWeb() {
  const { nodes, edges } = useMemo(() => {
    const people = ATTENDEES.slice(0, 10);
    const cx = 200;
    const cy = 200;
    const r = 150;
    const ns: Node[] = people.map((p, i) => {
      const angle = (i / people.length) * Math.PI * 2 - Math.PI / 2;
      return {
        id: p.id,
        name: p.name.split(" ")[0],
        interests: p.interests,
        x: cx + r * Math.cos(angle),
        y: cy + r * Math.sin(angle),
      };
    });
    const es: Edge[] = [];
    for (let i = 0; i < ns.length; i++) {
      for (let j = i + 1; j < ns.length; j++) {
        const s = overlap(ns[i].interests, ns[j].interests);
        if (s > 0) es.push({ from: ns[i].id, to: ns[j].id, strength: s });
      }
    }
    return { nodes: ns, edges: es };
  }, []);

  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));

  return (
    <div className="glass overflow-hidden p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink-900">Mutual interest map</h2>
        <span className="text-xs text-ink-faint">Red = stronger overlap</span>
      </div>
      <svg viewBox="0 0 400 400" className="mx-auto w-full max-w-md">
        {edges.map((e) => {
          const a = byId[e.from];
          const b = byId[e.to];
          const opacity = 0.15 + e.strength * 0.85;
          const width = 1 + e.strength * 3;
          return (
            <line
              key={`${e.from}-${e.to}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={`rgba(220, 38, 38, ${opacity})`}
              strokeWidth={width}
            />
          );
        })}
        <circle cx={200} cy={200} r={28} fill="#fff" stroke="#f97316" strokeWidth={2} />
        <text x={200} y={205} textAnchor="middle" className="fill-ink-900 text-[11px] font-bold">
          You
        </text>
        {nodes.map((n) => (
          <g key={n.id}>
            <circle cx={n.x} cy={n.y} r={22} fill="#fff" stroke="#ea580c" strokeWidth={1.5} />
            <text
              x={n.x}
              y={n.y + 4}
              textAnchor="middle"
              className="fill-ink-900 text-[10px] font-semibold"
            >
              {n.name}
            </text>
          </g>
        ))}
      </svg>
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {edges
          .sort((a, b) => b.strength - a.strength)
          .slice(0, 4)
          .map((e) => {
            const a = byId[e.from];
            const b = byId[e.to];
            const shared = a.interests.filter((i) =>
              b.interests.some((j) => j.toLowerCase() === i.toLowerCase()),
            );
            return (
              <div
                key={`${e.from}-${e.to}`}
                className="rounded-xl border border-red-brand/20 bg-red-brand/5 px-3 py-2"
              >
                <p className="text-xs font-semibold text-ink-900">
                  {a.name} ↔ {b.name}
                </p>
                <p className="mt-0.5 text-[11px] text-ink-muted">
                  Shared: {shared.join(", ") || "—"}
                </p>
              </div>
            );
          })}
      </div>
    </div>
  );
}

/** Compact avatar row for connection cards. */
export function PersonRow({
  name,
  company,
  title,
  interests,
}: {
  name: string;
  company: string;
  title?: string | null;
  score?: number;
  interests: string[];
}) {
  return (
    <div className="flex items-center gap-3">
      <Avatar name={name} size="md" />
      <div className="min-w-0 flex-1">
        <div className="font-semibold text-ink-900">{name}</div>
        <div className="text-xs text-ink-muted">
          {title ? `${title} · ` : ""}
          {company}
        </div>
        <div className="mt-1 flex flex-wrap gap-1">
          {interests.slice(0, 3).map((i) => (
            <span key={i} className="text-[10px] text-flame">
              {i}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
