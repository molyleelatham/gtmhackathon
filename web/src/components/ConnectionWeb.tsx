import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Toggle } from "./Toggle";
import { ATTENDEES } from "../lib/mockData";
import { personInitials } from "../lib/avatars";

interface PersonNode {
  id: string;
  name: string;
  fullName: string;
  interests: string[];
  icpScore: number;
}

interface Edge {
  from: string;
  to: string;
  usefulness: number;
  shared: string[];
}

interface SimNode {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
}

const NODE_R = 24;
const MIN_NODE_DIST = 132;
const LABEL_OFFSET = 46;
const LABEL_HEIGHT = 14;
const VIEW_PAD = 40;

const PEOPLE = ATTENDEES.slice(0, 8);

const ALL_INTERESTS = Array.from(
  new Set(PEOPLE.flatMap((p) => p.interests)),
).sort();

function overlap(a: string[], b: string[]): { strength: number; shared: string[] } {
  const setB = new Set(b.map((s) => s.toLowerCase()));
  const shared = a.filter((i) => setB.has(i.toLowerCase()));
  if (shared.length === 0) return { strength: 0, shared: [] };
  return {
    strength: shared.length / Math.max(a.length, b.length, 1),
    shared,
  };
}

/** Mutual usefulness: shared-interest overlap + average ICP fit. */
function usefulnessScore(
  a: Pick<PersonNode, "interests" | "icpScore">,
  b: Pick<PersonNode, "interests" | "icpScore">,
): { usefulness: number; shared: string[] } {
  const { strength, shared } = overlap(a.interests, b.interests);
  if (shared.length === 0) return { usefulness: 0, shared: [] };

  const interestPart = Math.min(1, shared.length / 3) * 0.55 + strength * 0.45;
  const icpPart = (a.icpScore + b.icpScore) / 200;
  const usefulness = interestPart * 0.55 + icpPart * 0.45;

  return { usefulness: Math.min(1, usefulness), shared };
}

function buildPeerEdges(people: PersonNode[]): Edge[] {
  const edges: Edge[] = [];
  for (let i = 0; i < people.length; i++) {
    for (let j = i + 1; j < people.length; j++) {
      const { usefulness, shared } = usefulnessScore(people[i], people[j]);
      if (usefulness > 0) {
        edges.push({ from: people[i].id, to: people[j].id, usefulness, shared });
      }
    }
  }
  return edges;
}

function spreadScale(nodeCount: number, filtered: boolean): number {
  if (!filtered) return 1;
  const fewer = Math.max(0, PEOPLE.length - nodeCount);
  return 1.45 + fewer * 0.12;
}

/** Grid + jitter seed so nodes start spread out, not in a tight ring. */
function seedPositions(
  nodeIds: string[],
  width: number,
  height: number,
  minDist: number,
): SimNode[] {
  const n = nodeIds.length;
  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  const cellW = minDist * 1.75;
  const cellH = minDist * 2;
  const gridW = (cols - 1) * cellW;
  const gridH = (rows - 1) * cellH;
  const ox = width / 2 - gridW / 2;
  const oy = height / 2 - gridH / 2;

  return nodeIds.map((id, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const jitter = minDist * 0.1;
    return {
      id,
      x: ox + col * cellW + (Math.random() - 0.5) * jitter,
      y: oy + row * cellH + (Math.random() - 0.5) * jitter,
      vx: 0,
      vy: 0,
    };
  });
}

function layoutCanvasSize(
  nodeCount: number,
  minDist: number,
): { width: number; height: number } {
  const cols = Math.ceil(Math.sqrt(Math.max(nodeCount, 1)));
  const rows = Math.ceil(nodeCount / cols);
  const width = Math.max(480, cols * minDist * 1.75 + NODE_R * 2 + VIEW_PAD * 2);
  const height = Math.max(
    480,
    rows * minDist * 2 + NODE_R + LABEL_OFFSET + LABEL_HEIGHT + VIEW_PAD * 2,
  );
  return { width, height };
}

function applyRepulsion(nodes: SimNode[], cooling: number, minDist: number) {
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i];
      const b = nodes[j];
      let dx = a.x - b.x;
      let dy = a.y - b.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;

      const repulse = (42000 * cooling) / (dist * dist);
      let fx = (dx / dist) * repulse;
      let fy = (dy / dist) * repulse;

      if (dist < minDist) {
        const push = ((minDist - dist) / minDist) * 3.4 * cooling;
        fx += (dx / dist) * push * 180;
        fy += (dy / dist) * push * 180;
      }

      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    }
  }
}

function applyEdgeAttraction(edges: Edge[], byId: Record<string, SimNode>, cooling: number) {
  for (const e of edges) {
    const a = byId[e.from];
    const b = byId[e.to];
    if (!a || !b) continue;
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const ideal = 130 + (1 - e.usefulness) * 70;
    const force = (dist - ideal) * 0.04 * (0.25 + e.usefulness) * cooling;
    a.vx += (dx / dist) * force;
    a.vy += (dy / dist) * force;
    b.vx -= (dx / dist) * force;
    b.vy -= (dy / dist) * force;
  }
}

/** Force-directed layout — strong repulsion, min distance, weak center pull. */
function computeForceLayout(
  nodeIds: string[],
  edges: Edge[],
  filtered: boolean,
): Record<string, { x: number; y: number }> {
  if (nodeIds.length === 0) return {};

  const scale = spreadScale(nodeIds.length, filtered);
  const minDist = MIN_NODE_DIST * scale;
  const { width, height } = layoutCanvasSize(nodeIds.length, minDist);
  const cx = width / 2;
  const cy = height / 2;
  const nodes = seedPositions(nodeIds, width, height, minDist);
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const iterations = nodeIds.length <= 3 ? 120 : 220;

  for (let iter = 0; iter < iterations; iter++) {
    const cooling = 1 - iter / iterations;

    for (const n of nodes) {
      n.vx *= 0.52;
      n.vy *= 0.52;
    }

    applyRepulsion(nodes, cooling, minDist);
    applyEdgeAttraction(edges, byId, cooling);

    for (const n of nodes) {
      n.vx += (cx - n.x) * 0.006;
      n.vy += (cy - n.y) * 0.006;
    }

    for (const n of nodes) {
      n.x += n.vx * 0.13;
      n.y += n.vy * 0.13;
    }
  }

  return Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }]));
}

/** Gentle post-drag relaxation — keeps fixed node, separates overlaps. */
function relaxAfterDrag(
  positions: Record<string, { x: number; y: number }>,
  nodeIds: string[],
  fixedId: string,
  filtered: boolean,
): Record<string, { x: number; y: number }> {
  const minDist = MIN_NODE_DIST * spreadScale(nodeIds.length, filtered);
  const nodes: SimNode[] = nodeIds.map((id) => ({
    id,
    x: positions[id]?.x ?? 0,
    y: positions[id]?.y ?? 0,
    vx: 0,
    vy: 0,
  }));
  const fixed = nodes.find((n) => n.id === fixedId);

  for (let iter = 0; iter < 28; iter++) {
    const cooling = 1 - iter / 28;
    for (const n of nodes) {
      n.vx = 0;
      n.vy = 0;
    }

    applyRepulsion(nodes, cooling * 0.5, minDist);

    for (const n of nodes) {
      if (n.id === fixedId) continue;
      n.x += n.vx * 0.2;
      n.y += n.vy * 0.2;
    }

    if (fixed) {
      fixed.x = positions[fixedId].x;
      fixed.y = positions[fixedId].y;
    }
  }

  return Object.fromEntries(nodes.map((n) => [n.id, { x: n.x, y: n.y }]));
}

function computeViewBox(
  positions: Record<string, { x: number; y: number }>,
  nodeIds: string[],
): string {
  const coords = nodeIds.map((id) => positions[id]).filter(Boolean);
  if (coords.length === 0) return "0 0 520 520";

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const { x, y } of coords) {
    minX = Math.min(minX, x - NODE_R - 44);
    maxX = Math.max(maxX, x + NODE_R + 44);
    minY = Math.min(minY, y - NODE_R - 24);
    maxY = Math.max(maxY, y + LABEL_OFFSET + LABEL_HEIGHT + 12);
  }

  minX -= VIEW_PAD;
  minY -= VIEW_PAD;
  maxX += VIEW_PAD;
  maxY += VIEW_PAD;

  const width = Math.max(maxX - minX, 320);
  const height = Math.max(maxY - minY, 320);

  return `${minX} ${minY} ${width} ${height}`;
}

/** Strong mutual fit → dark red; weak overlap → pale pink. */
function edgeStroke(usefulness: number): { color: string; width: number; opacity: number } {
  const t = Math.min(1, Math.max(0, usefulness));
  const r = Math.round(255 - t * (255 - 220));
  const g = Math.round(228 - t * (228 - 38));
  const b = Math.round(228 - t * (228 - 38));
  return {
    color: `rgb(${r}, ${g}, ${b})`,
    width: 0.75 + t * 4.25,
    opacity: 0.18 + t * 0.78,
  };
}

function interestEdgeCount(edges: Edge[], interest: string): number {
  const key = interest.toLowerCase();
  return edges.filter((e) => e.shared.some((s) => s.toLowerCase() === key)).length;
}

export function ConnectionWeb() {
  const [filterEnabled, setFilterEnabled] = useState(false);
  const [interestFilter, setInterestFilter] = useState<string | null>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const dragRef = useRef<{ id: string; startX: number; startY: number; nodeX: number; nodeY: number } | null>(
    null,
  );

  const people: PersonNode[] = useMemo(
    () =>
      PEOPLE.map((p) => ({
        id: p.id,
        name: p.name.split(" ")[0],
        fullName: p.name,
        interests: p.interests,
        icpScore: p.icpScore,
      })),
    [],
  );

  const allEdges = useMemo(() => buildPeerEdges(people), [people]);

  const filteredEdges = useMemo(() => {
    if (!filterEnabled || !interestFilter) return allEdges;
    const key = interestFilter.toLowerCase();
    return allEdges.filter((e) => e.shared.some((s) => s.toLowerCase() === key));
  }, [allEdges, filterEnabled, interestFilter]);

  const visibleNodeIds = useMemo(() => {
    if (!filterEnabled || !interestFilter) return people.map((p) => p.id);
    const ids = new Set<string>();
    filteredEdges.forEach((e) => {
      ids.add(e.from);
      ids.add(e.to);
    });
    return [...ids];
  }, [people, filterEnabled, interestFilter, filteredEdges]);

  const isFilteredView = filterEnabled && interestFilter !== null;

  const layoutPositions = useMemo(
    () => computeForceLayout(visibleNodeIds, filteredEdges, isFilteredView),
    [visibleNodeIds, filteredEdges, isFilteredView],
  );

  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});

  useEffect(() => {
    setPositions(layoutPositions);
  }, [layoutPositions]);

  const viewBox = useMemo(
    () => computeViewBox(positions, visibleNodeIds),
    [positions, visibleNodeIds],
  );

  const clientToSvg = useCallback((clientX: number, clientY: number) => {
    const svg = svgRef.current;
    if (!svg) return { x: 0, y: 0 };
    const pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    const ctm = svg.getScreenCTM();
    if (!ctm) return { x: 0, y: 0 };
    const { x, y } = pt.matrixTransform(ctm.inverse());
    return { x, y };
  }, []);

  const onPointerDown = useCallback(
    (id: string, e: React.PointerEvent) => {
      const pos = positions[id];
      if (!pos) return;
      e.currentTarget.setPointerCapture(e.pointerId);
      const { x, y } = clientToSvg(e.clientX, e.clientY);
      dragRef.current = { id, startX: x, startY: y, nodeX: pos.x, nodeY: pos.y };
    },
    [positions, clientToSvg],
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent) => {
      const drag = dragRef.current;
      if (!drag) return;
      const { x, y } = clientToSvg(e.clientX, e.clientY);
      const dx = x - drag.startX;
      const dy = y - drag.startY;
      setPositions((prev) => ({
        ...prev,
        [drag.id]: { x: drag.nodeX + dx, y: drag.nodeY + dy },
      }));
    },
    [clientToSvg],
  );

  const onPointerUp = useCallback(() => {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag) return;

    setPositions((prev) => {
      const ids = Object.keys(prev).filter((id) => visibleNodeIds.includes(id));
      if (ids.length < 2) return prev;
      return relaxAfterDrag(prev, ids, drag.id, isFilteredView);
    });
  }, [visibleNodeIds, isFilteredView]);

  const handleFilterToggle = (on: boolean) => {
    setFilterEnabled(on);
    setInterestFilter(on ? ALL_INTERESTS[0] : null);
  };

  const activeFilter = filterEnabled ? interestFilter : null;

  return (
    <div className="glass overflow-hidden p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-ink-900">Mutual interest map</h2>
          <p className="text-[11px] text-ink-faint">
            Darker lines = stronger mutual fit · drag nodes to rearrange
          </p>
        </div>
        <Toggle label="Filter by interest" checked={filterEnabled} onChange={handleFilterToggle} />
      </div>

      {filterEnabled && (
        <div className="mb-3">
          <p className="mb-1.5 text-[10px] font-medium uppercase tracking-wide text-ink-faint">
            Shared interest
          </p>
          <div className="flex flex-wrap gap-1.5">
            {ALL_INTERESTS.map((interest) => {
              const count = interestEdgeCount(allEdges, interest);
              const selected = interestFilter === interest;
              return (
                <button
                  key={interest}
                  type="button"
                  onClick={() => setInterestFilter(interest)}
                  className={`glass-pill transition-colors ${
                    selected
                      ? "border-red-brand/40 bg-red-brand/15 text-red-brand"
                      : count === 0
                        ? "border-subtle text-ink-faint"
                        : "border-subtle text-ink-muted"
                  }`}
                  disabled={count === 0}
                  title={count === 0 ? "No connections for this interest" : `${count} connection${count === 1 ? "" : "s"}`}
                >
                  {interest}
                  {count > 0 && (
                    <span
                      className={`ml-1 tabular-nums ${selected ? "text-red-brand/80" : "text-ink-faint"}`}
                    >
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <svg
        ref={svgRef}
        viewBox={viewBox}
        className="mx-auto w-full max-w-lg touch-none select-none"
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      >
        {filteredEdges.map((e) => {
          const a = positions[e.from];
          const b = positions[e.to];
          if (!a || !b) return null;
          const { color, width, opacity } = edgeStroke(e.usefulness);
          return (
            <line
              key={`${e.from}-${e.to}`}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              stroke={color}
              strokeWidth={width}
              strokeOpacity={opacity}
              strokeLinecap="round"
            />
          );
        })}

        {people.map((n) => {
          const pos = positions[n.id];
          if (!pos || !visibleNodeIds.includes(n.id)) return null;
          return (
            <g
              key={n.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              className="cursor-grab active:cursor-grabbing"
              onPointerDown={(e) => onPointerDown(n.id, e)}
            >
              <circle
                r={NODE_R}
                className="fill-[var(--surface-page)] stroke-flame"
                strokeWidth={1.5}
              />
              <text
                y={4}
                textAnchor="middle"
                className="pointer-events-none text-[10px] font-semibold"
                fill="var(--ink-primary)"
              >
                {personInitials(n.fullName)}
              </text>
              <text
                y={LABEL_OFFSET}
                textAnchor="middle"
                className="pointer-events-none text-[9px]"
                fill="var(--ink-secondary)"
              >
                {n.name}
              </text>
            </g>
          );
        })}
      </svg>

      {activeFilter && (
        <p className="mt-2 text-center text-[11px] text-ink-muted">
          {visibleNodeIds.length === 0 ? (
            <>No connections share <strong className="text-ink-900">{activeFilter}</strong></>
          ) : (
            <>
              <strong className="text-ink-900">{visibleNodeIds.length}</strong>{" "}
              {visibleNodeIds.length === 1 ? "person" : "people"} connected via{" "}
              <strong className="text-ink-900">{activeFilter}</strong>
              {filteredEdges.length > 0 && (
                <>
                  {" "}
                  · <strong className="text-ink-900">{filteredEdges.length}</strong>{" "}
                  {filteredEdges.length === 1 ? "link" : "links"}
                </>
              )}
            </>
          )}
        </p>
      )}

      {!activeFilter && allEdges.length === 0 && (
        <p className="mt-2 text-center text-[11px] text-ink-faint">No shared interests in this group yet.</p>
      )}
    </div>
  );
}
