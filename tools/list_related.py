"""List nodes that have given relationship(s) to a node (by node_id)."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import get_allowed_labels, get_driver

from tools._shared import build_validity_clause


def list_related(
    start_node_id: str,
    relationship_types: list[str],
    target_label: Optional[str] = None,
    validity_filter: Optional[dict[str, Any]] = None,
    limit: int = 1000,
    include_attributes: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    List nodes that have INCOMING relationships of the given types TO the start node
    (use node_id from find_node). E.g. list entities in a location:
    relationship_types=["LOCATED_IN"], target_label="Asset".
    Use include_attributes=None for full node details; pass a list to restrict.
    """
    allowed_labels = get_allowed_labels()
    if target_label is not None and target_label not in allowed_labels:
        return {"error": f"target_label must be one of {sorted(allowed_labels)}"}

    validity_clause, as_of_date = build_validity_clause(validity_filter)
    rel_types = "|".join(relationship_types) if relationship_types else ""
    if not rel_types:
        return {"error": "relationship_types cannot be empty"}
    target_label_clause = f":{target_label}" if target_label else ""
    pattern = f"(target{target_label_clause})-[r:{rel_types}]->(start)"

    match_start = "MATCH (start) WHERE elementId(start) = $start_node_id"
    params: dict[str, Any] = {"start_node_id": start_node_id, "limit": limit}
    if as_of_date:
        params["as_of_date"] = as_of_date

    driver = get_driver()
    with driver.session() as session:
        query = f"""
        {match_start}
        MATCH {pattern}
        WHERE 1=1 {validity_clause}
        RETURN target, elementId(target) AS target_id
        LIMIT $limit
        """
        result = session.run(query, params)
        nodes = []
        for record in result:
            target = record.get("target")
            if target:
                d = dict(target)
                d["node_id"] = record.get("target_id")
                if include_attributes:
                    d = {k: d.get(k) for k in include_attributes if k in d}
                nodes.append(d)
        return {
            "result": nodes,
            "relationship_count": len(nodes),
            "target_nodes_found": len(nodes),
        }
