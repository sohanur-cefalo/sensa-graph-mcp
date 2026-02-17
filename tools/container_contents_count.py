"""Count nodes that point into a given node (by node_id)."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import ALLOWED_LABELS, get_driver

from tools._shared import build_validity_clause


def container_contents_count(
    start_node_id: str,
    relationship_types: list[str],
    target_label: Optional[str] = None,
    validity_filter: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Count nodes that have INCOMING relationships of the given types TO the start node
    (use node_id from get_node_by_name). E.g. assets LOCATED_IN a location:
    relationship_types=["LOCATED_IN"], target_label="Asset".
    """
    if target_label is not None and target_label not in ALLOWED_LABELS:
        return {"error": f"target_label must be one of {sorted(ALLOWED_LABELS)}"}

    validity_clause, as_of_date = build_validity_clause(validity_filter)
    rel_types = "|".join(relationship_types) if relationship_types else ""
    if not rel_types:
        return {"error": "relationship_types cannot be empty"}
    target_label_clause = f":{target_label}" if target_label else ""
    pattern = f"(target{target_label_clause})-[r:{rel_types}]->(start)"

    match_start = "MATCH (start) WHERE elementId(start) = $start_node_id"
    params: dict[str, Any] = {"start_node_id": start_node_id}
    if as_of_date:
        params["as_of_date"] = as_of_date

    driver = get_driver()
    with driver.session() as session:
        query = f"""
        {match_start}
        MATCH {pattern}
        WHERE 1=1 {validity_clause}
        RETURN count(target) AS result, count(r) AS rel_count
        """
        result = session.run(query, params)
        row = result.single()
        return {
            "result": row["result"] if row else 0,
            "relationship_count": row["rel_count"] if row else 0,
            "target_nodes_found": row["result"] if row else 0,
        }
