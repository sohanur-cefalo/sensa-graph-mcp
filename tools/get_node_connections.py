"""Get how a node is connected: incoming and outgoing relationships."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import get_driver, get_node_by_name_labels

from tools._shared import node_to_dict


def get_node_connections(
    name: str,
    include_attributes: bool = False,
) -> dict[str, Any]:
    """
    For a node found by name (any available node type), list all
    incoming and outgoing relationships: type and the other node's name/label.
    Use for: "How is X connected?", "What is inside X?",
    "How is X connected with others?", "What links to X?".
    """
    driver = get_driver()
    labels = get_node_by_name_labels()
    with driver.session() as session:
        # Resolve name to node (same order as find_node)
        node_id: Optional[str] = None
        node_label: Optional[str] = None
        node_attrs: dict[str, Any] = {}

        for lbl in labels:
            query = (
                f"MATCH (n:{lbl}) WHERE toLower(n.name) = toLower($name) "
                "RETURN n LIMIT 1"
            )
            result = session.run(query, name=name)
            record = result.single()
            if record:
                out = node_to_dict(record)
                node_id = out.get("node_id")
                node_label = out.get("label") or lbl
                node_attrs = out.get("attributes") or {}
                break

        if not node_id:
            searched_labels = ", ".join(labels)
            return {
                "found": False,
                "name": name,
                "node_id": None,
                "incoming": [],
                "outgoing": [],
                "message": f"No node found with this name (searched {searched_labels}).",
            }

        # Outgoing: (start)-[r]->(other)
        q_out = """
        MATCH (start) WHERE elementId(start) = $node_id
        MATCH (start)-[r]->(other)
        RETURN type(r) AS rel_type, other.name AS other_name,
               labels(other)[0] AS other_label, other.fingerprint AS other_fingerprint
        ORDER BY type(r), other.name
        """
        result = session.run(q_out, node_id=node_id)
        outgoing = [
            {
                "relationship_type": r["rel_type"],
                "target_name": r["other_name"],
                "target_label": r["other_label"],
                "target_fingerprint": r["other_fingerprint"],
            }
            for r in result
        ]

        # Incoming: (other)-[r]->(start)
        q_in = """
        MATCH (start) WHERE elementId(start) = $node_id
        MATCH (other)-[r]->(start)
        RETURN type(r) AS rel_type, other.name AS other_name,
               labels(other)[0] AS other_label, other.fingerprint AS other_fingerprint
        ORDER BY type(r), other.name
        """
        result = session.run(q_in, node_id=node_id)
        incoming = [
            {
                "relationship_type": r["rel_type"],
                "source_name": r["other_name"],
                "source_label": r["other_label"],
                "source_fingerprint": r["other_fingerprint"],
            }
            for r in result
        ]

        out: dict[str, Any] = {
            "found": True,
            "name": name,
            "node_id": node_id,
            "label": node_label,
            "incoming": incoming,
            "outgoing": outgoing,
            "incoming_count": len(incoming),
            "outgoing_count": len(outgoing),
        }
        if include_attributes:
            out["attributes"] = node_attrs
        return out
