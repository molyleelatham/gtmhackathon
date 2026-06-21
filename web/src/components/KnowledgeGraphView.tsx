import { useMemo } from "react";
import type { WarmthBand } from "../types";
import { Acronym } from "./Acronym";

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  kind: "person" | "interest" | "value" | "topic" | "style" | "pain";
  weight?: number;
  dominant?: boolean;
}

export interface KnowledgeGraphEdge {
  from: string;
  to: string;
  strength?: number;
}

export interface KnowledgeGraphViewProps {
  personName: string;
  interests?: string[];
  topicWeights?: Record<string, number>;
  values?: string[];
  /** Personal context (from the meet-stage PersonNode). */
  communicationStyle?: string[];
  painPoints?: { topic: string; intensity: number }[];
  dominantTopic?: string;
  /** ML fields (from the WarmthScore / pre-meet scoring). */
  warmthScore?: number;
  icpScore?: number;
  band?: WarmthBand;
  className?: string;
  height?: number;
}

// rgb triplets so we can tint SVG fills/strokes and CSS alike.
const NODE_RGB = {
  topic: "255 120 60",
  interest: "255 180 100",
  value: "220 80 90",
  style: "150 120 240",
  pain: "240 70 90",
} as const;

const BAND_RGB: Record<WarmthBand, string> = {
  hot: "255 90 70",
  warm: "255 165 70",
  cold: "120 175 255",
};

function polar(cx: number, cy: number, r: number, angle: number) {
  return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
}

export function KnowledgeGraphView({
  personName,
  interests = [],
  topicWeights,
  values = [],
  communicationStyle = [],
  painPoints = [],
  dominantTopic,
  warmthScore,
  icpScore,
  band,
  className = "",
  height = 320,
}: KnowledgeGraphViewProps) {
  const graph = useMemo(() => {
    const nodes: KnowledgeGraphNode[] = [
      { id: "person", label: personName, kind: "person" },
    ];
    const edges: KnowledgeGraphEdge[] = [];

    const topicEntries = topicWeights
      ? Object.entries(topicWeights).sort((a, b) => b[1] - a[1])
      : [];
    const topicLabels = topicEntries.map(([t]) => t);
    const interestLabels = interests.filter(
      (i) => !topicLabels.some((t) => t.toLowerCase() === i.toLowerCase()),
    );
    const topDominant =
      dominantTopic?.toLowerCase() ?? topicLabels[0]?.toLowerCase();

    topicEntries.forEach(([label, weight], i) => {
      const id = `topic-${i}`;
      nodes.push({
        id,
        label,
        kind: "topic",
        weight,
        dominant: label.toLowerCase() === topDominant,
      });
      edges.push({ from: "person", to: id, strength: weight });
    });

    interestLabels.forEach((label, i) => {
      const id = `interest-${i}`;
      nodes.push({ id, label, kind: "interest" });
      edges.push({ from: "person", to: id, strength: 0.5 });
    });

    values.forEach((label, i) => {
      const id = `value-${i}`;
      nodes.push({ id, label, kind: "value" });
      edges.push({ from: "person", to: id, strength: 0.35 });
    });

    communicationStyle.forEach((label, i) => {
      const id = `style-${i}`;
      nodes.push({ id, label, kind: "style" });
      edges.push({ from: "person", to: id, strength: 0.45 });
    });

    painPoints.forEach((p, i) => {
      const id = `pain-${i}`;
      nodes.push({ id, label: p.topic, kind: "pain", weight: p.intensity });
      edges.push({ from: "person", to: id, strength: 0.3 + p.intensity * 0.5 });
    });

    return { nodes, edges };
  }, [personName, interests, topicWeights, values, communicationStyle, painPoints, dominantTopic]);

  const width = 420;
  const cx = width / 2;
  const cy = height / 2;
  const outerNodes = graph.nodes.filter((n) => n.id !== "person");
  const radius = Math.min(width, height) * 0.34;
  const personRgb = band ? BAND_RGB[band] : "255 120 60";

  const positions = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {
      person: { x: cx, y: cy },
    };
    outerNodes.forEach((node, i) => {
      const angle = (i / Math.max(outerNodes.length, 1)) * Math.PI * 2 - Math.PI / 2;
      const r = node.kind === "topic" ? radius * 0.92 : radius;
      map[node.id] = polar(cx, cy, r, angle);
    });
    return map;
  }, [outerNodes, cx, cy, radius]);

  const hasMl = warmthScore != null || icpScore != null || band != null;

  if (outerNodes.length === 0) {
    return (
      <div className={`glass flex items-center justify-center p-6 text-sm text-ink-faint ${className}`} style={{ height }}>
        Capture a conversation to build the interest graph.
      </div>
    );
  }

  return (
    <div className={`glass overflow-hidden ${className}`}>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-full w-full" role="img" aria-label={`Knowledge graph for ${personName}`}>
        <defs>
          <radialGradient id="kg-person-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={`rgb(${personRgb} / 0.4)`} />
            <stop offset="100%" stopColor={`rgb(${personRgb} / 0)`} />
          </radialGradient>
        </defs>

        {graph.edges.map((edge) => {
          const a = positions[edge.from];
          const b = positions[edge.to];
          if (!a || !b) return null;
          const target = graph.nodes.find((n) => n.id === edge.to);
          const rgb = target ? NODE_RGB[target.kind as keyof typeof NODE_RGB] ?? personRgb : personRgb;
          const stroke = 0.2 + (edge.strength ?? 0.4) * 0.55;
          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={`rgb(${rgb})`}
              strokeOpacity={stroke}
              strokeWidth={1 + (edge.strength ?? 0.3) * 2}
            />
          );
        })}

        <circle cx={cx} cy={cy} r={52} fill="url(#kg-person-glow)" />

        {outerNodes.map((node) => {
          const p = positions[node.id];
          if (!p) return null;
          const rgb = NODE_RGB[node.kind as keyof typeof NODE_RGB] ?? "255 180 100";
          const baseR =
            node.kind === "topic" || node.kind === "pain"
              ? 9 + (node.weight ?? 0.2) * 14
              : 9;
          return (
            <g key={node.id}>
              {node.dominant && (
                <circle cx={p.x} cy={p.y} r={baseR + 4} fill="none" stroke={`rgb(${rgb})`} strokeOpacity={0.7} strokeWidth={1.5} />
              )}
              <circle cx={p.x} cy={p.y} r={baseR} fill={`rgb(${rgb} / 0.85)`} />
              <text
                x={p.x}
                y={p.y + baseR + 12}
                textAnchor="middle"
                className="fill-ink-muted text-[9px] font-medium"
              >
                {node.label.length > 16 ? `${node.label.slice(0, 15)}…` : node.label}
              </text>
            </g>
          );
        })}

        <circle cx={cx} cy={cy} r={28} fill={`rgb(${personRgb} / 0.22)`} stroke={`rgb(${personRgb} / 0.6)`} strokeWidth={1.5} />
        <text x={cx} y={warmthScore != null ? cy - 1 : cy + 4} textAnchor="middle" className="fill-ink-900 text-[11px] font-bold">
          {personName.split(" ")[0]}
        </text>
        {warmthScore != null && (
          <text x={cx} y={cy + 11} textAnchor="middle" className="fill-ink-muted text-[8px] font-semibold">
            {Math.round(warmthScore)}
          </text>
        )}
      </svg>

      {hasMl && (
        <div className="flex flex-wrap items-center gap-2 border-t border-subtle px-3 py-2 text-[10px]">
          {band && (
            <span className="glass-pill" style={{ color: `rgb(${BAND_RGB[band]})` }}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {band.toUpperCase()}
              {warmthScore != null ? ` · ${Math.round(warmthScore)}` : ""}
            </span>
          )}
          {icpScore != null && (
            <span className="text-ink-muted">
              <Acronym term="ICP">ICP</Acronym>{" "}
              <span className="font-semibold text-ink-900">{Math.round(icpScore)}</span>
            </span>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-x-3 gap-y-1 border-t border-subtle px-3 py-2 text-[10px] text-ink-faint">
        <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: `rgb(${NODE_RGB.topic})` }} /> Topics</span>
        <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: `rgb(${NODE_RGB.interest})` }} /> Interests</span>
        <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: `rgb(${NODE_RGB.value})` }} /> Values</span>
        {communicationStyle.length > 0 && (
          <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: `rgb(${NODE_RGB.style})` }} /> Style</span>
        )}
        {painPoints.length > 0 && (
          <span className="inline-flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: `rgb(${NODE_RGB.pain})` }} /> Pain points</span>
        )}
      </div>
    </div>
  );
}
