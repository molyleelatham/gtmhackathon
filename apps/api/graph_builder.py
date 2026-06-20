"""Build interest knowledge graphs for the web dashboard."""
from __future__ import annotations

from typing import Any

from ....packages.core.models.pre_connection import PreMeetConnection


def _slug(label: str) -> str:
    return label.lower().strip().replace(" ", "_").replace("/", "_")


def _interest_node_id(label: str, kind: str = "interest") -> str:
    return f"{kind}:{_slug(label)}"


def person_graph_from_connection(
    conn: PreMeetConnection,
    kg_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Single-person graph: person node + every interest/topic/value/pain node."""
    person_id = conn.id
    interest_nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def link(label: str, kind: str, weight: float = 1.0) -> None:
        if not label or not str(label).strip():
            return
        text = str(label).strip()
        nid = _interest_node_id(text, kind)
        if nid not in interest_nodes:
            interest_nodes[nid] = {
                "id": nid,
                "label": text,
                "kind": kind,
                "weight": weight,
            }
        else:
            interest_nodes[nid]["weight"] = max(interest_nodes[nid]["weight"], weight)
        edges.append(
            {
                "from": person_id,
                "to": nid,
                "weight": round(weight, 3),
                "kind": kind,
            }
        )

    for interest in conn.interests:
        link(interest, "interest", 1.0)

    for note in conn.research_notes or []:
        link(note[:80], "signal", 0.85)

    for tech in getattr(conn, "technographics", None) or []:
        link(tech, "tech", 0.9)

    primary_person: dict[str, Any] | None = None
    if kg_payload:
        people = kg_payload.get("people") or []
        if kg_payload.get("person"):
            people = [kg_payload["person"], *people]
        for raw in people:
            if raw.get("is_self"):
                continue
            primary_person = raw
            for topic, w in (raw.get("topic_weights") or {}).items():
                link(topic, "topic", float(w))
            for val in raw.get("values") or []:
                link(val, "value", 0.75)
            for style in raw.get("communication_style") or []:
                link(style, "style", 0.7)
            for learning in raw.get("learnings") or []:
                link(learning[:60], "learning", 0.8)
            for pain in raw.get("pain_points") or []:
                topic = pain.get("topic") if isinstance(pain, dict) else str(pain)
                intensity = float(pain.get("intensity", 0.5) if isinstance(pain, dict) else 0.5)
                link(topic, "pain", intensity)
            break

    person = {
        "id": person_id,
        "name": conn.name or "Unknown",
        "company": conn.company_name,
        "title": conn.title,
        "icpScore": int(conn.icp_score),
        "interests": list(conn.interests),
        "narrative": (kg_payload or {}).get("narrative"),
        "personNode": primary_person,
    }

    return {
        "person": person,
        "interest_nodes": list(interest_nodes.values()),
        "edges": edges,
    }


def build_roster_graph(
    connections: list[PreMeetConnection],
    knowledge_by_connection: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Conference roster graph — every person linked to ALL their interests; peer edges on overlap."""
    people: list[dict[str, Any]] = []
    interest_nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    person_interest_sets: dict[str, set[str]] = {}

    for conn in connections:
        sub = person_graph_from_connection(conn, knowledge_by_connection.get(conn.id))
        people.append(sub["person"])
        person_interest_sets[conn.id] = set()

        for node in sub["interest_nodes"]:
            interest_nodes[node["id"]] = node
            person_interest_sets[conn.id].add(node["label"].lower())

        for edge in sub["edges"]:
            edges.append(edge)

    # Person ↔ person edges weighted by shared interest count
    for i, a in enumerate(connections):
        for b in connections[i + 1 :]:
            shared = person_interest_sets[a.id] & person_interest_sets[b.id]
            if not shared:
                continue
            usefulness = min(1.0, len(shared) / 3)
            edges.append(
                {
                    "from": a.id,
                    "to": b.id,
                    "weight": round(usefulness, 3),
                    "kind": "peer",
                    "shared": sorted(shared),
                }
            )

    return {
        "people": people,
        "interest_nodes": list(interest_nodes.values()),
        "edges": edges,
    }
