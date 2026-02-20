"""Find nodes by name across all node types."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import get_driver, get_node_by_name_labels

from tools._shared import node_to_dict


def find_node(
    name: str,
    include_attributes: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Find all nodes with the given name attribute. Searches across all available node labels in priority order.
    Use this to get node_id(s) for count_related or list_related.
    For existence/count questions like "Do we have any X?", prefer count_nodes.
    Returns all matching nodes (nodes list); use nodes[0] for a single-node workflow if only one is expected.
    """
    driver = get_driver()
    labels = get_node_by_name_labels()
    seen_node_ids: set[str] = set()
    nodes: list[dict[str, Any]] = []
    with driver.session() as session:
        for lbl in labels:
            query = (
                f"MATCH (n:{lbl}) WHERE toLower(n.name) = toLower($name) RETURN n"
            )
            result = session.run(query, name=name)
            for record in result:
                out = node_to_dict(record)
                node_id = out.get("node_id")
                if node_id and node_id not in seen_node_ids:
                    seen_node_ids.add(node_id)
                    if include_attributes and out.get("attributes"):
                        out["attributes"] = {
                            k: out["attributes"][k]
                            for k in include_attributes
                            if k in out["attributes"]
                        }
                    out["label"] = lbl
                    nodes.append(out)
    if not nodes:
        return {"found": False, "nodes": [], "total_count": 0}
    return {
        "found": True,
        "nodes": nodes,
        "total_count": len(nodes),
    }
