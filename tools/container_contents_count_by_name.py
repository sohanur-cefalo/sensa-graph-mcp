"""Count nodes that point into container(s) found by name (e.g. assets in a location/system)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from neo4j_config import get_allowed_labels, get_driver, get_node_by_name_labels

from tools._shared import (
    build_validity_clause,
    format_count_summary_table,
    name_where_condition,
    node_to_dict,
)


def container_contents_count_by_name(
    name: str,
    relationship_types: list[str],
    target_label: Optional[str] = None,
    label: Optional[str] = None,
    name_match: Literal["exact", "prefix"] = "exact",
    parent_location_name: Optional[str] = None,
    validity_filter: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Find ALL nodes matching the given name, then for EACH
    count nodes that have INCOMING relationships of the given types to that node.
    Use for "How many assets in Biofilter 11?" (exact) or "How many items in Biofilter?"
    (prefix). Returns per-node breakdown and summary_table with total.
    """
    allowed_labels = get_allowed_labels()
    if target_label is not None and target_label not in allowed_labels:
        return {"error": f"target_label must be one of {sorted(allowed_labels)}"}
    if label is not None and label not in allowed_labels:
        return {"error": f"label must be one of {sorted(allowed_labels)} or null"}

    validity_clause, as_of_date = build_validity_clause(validity_filter)
    labels_to_try = [label] if label else list(get_node_by_name_labels())
    rel_types = "|".join(relationship_types) if relationship_types else []
    if not rel_types:
        return {"error": "relationship_types cannot be empty"}
    target_label_clause = f":{target_label}" if target_label else ""
    name_cond = name_where_condition(name_match)

    parent_clause = ""
    parent_params: dict[str, Any] = {}
    if parent_location_name:
        parent_clause = (
            " AND EXISTS { (n)-[:LOCATED_IN*]->(parent) "
            "WHERE (parent:Location OR parent:Context) AND toLower(parent.name) = toLower($parent_name) }"
        )
        parent_params = {"parent_name": parent_location_name}

    driver = get_driver()
    with driver.session() as session:
        start_nodes: list[dict[str, Any]] = []
        seen_node_ids: set[str] = set()  # Deduplicate by node_id to avoid double-counting nodes with multiple labels
        for lbl in labels_to_try:
            # Apply parent filter to Location and Context nodes (both can be locations)
            use_parent = parent_location_name and lbl in ("Location", "Context")
            q = (
                f"MATCH (n:{lbl}) WHERE {name_cond}"
                f"{parent_clause if use_parent else ''} RETURN n"
            )
            params: dict[str, Any] = {"name": name, **parent_params} if use_parent else {"name": name}
            result = session.run(q, params)
            for record in result:
                out = node_to_dict(record)
                node_id = out.get("node_id")
                if node_id and node_id not in seen_node_ids:
                    seen_node_ids.add(node_id)
                    out["label"] = lbl
                    start_nodes.append(out)

        if not start_nodes:
            return {
                "name": name,
                "found": False,
                "per_node": [],
                "total_result": 0,
                "total_relationship_count": 0,
                "total_count": 0,
                "summary_table": format_count_summary_table([], 0),
            }

        params = {}
        if as_of_date:
            params["as_of_date"] = as_of_date

        per_node: list[dict[str, Any]] = []
        total_result = 0
        total_rel_count = 0

        for node_info in start_nodes:
            node_id = node_info.get("node_id")
            if not node_id:
                continue
            match_start = "MATCH (start) WHERE elementId(start) = $start_node_id"
            pattern = f"(target{target_label_clause})-[r:{rel_types}]->(start)"
            params["start_node_id"] = node_id

            query = f"""
            {match_start}
            MATCH {pattern}
            WHERE 1=1 {validity_clause}
            RETURN count(target) AS result, count(r) AS rel_count
            """
            result = session.run(query, params)
            row = result.single()
            cnt = row["result"] if row else 0
            rel_count = row["rel_count"] if row else 0
            attrs = node_info.get("attributes") or {}
            per_node.append({
                "node_id": node_id,
                "label": node_info.get("label"),
                "fingerprint": attrs.get("fingerprint"),
                "attributes": attrs,
                "result": cnt,
                "relationship_count": rel_count,
            })
            total_result += cnt
            total_rel_count += rel_count

        container_label = (per_node[0].get("label") or "Container") if per_node else "Container"
        count_column = "Assets" if target_label == "Asset" else "Count"
        summary_table = format_count_summary_table(
            per_node, total_result, container_label=container_label, count_column=count_column
        )

        return {
            "name": name,
            "found": True,
            "nodes_count": len(start_nodes),
            "per_node": per_node,
            "total_result": total_result,
            "total_relationship_count": total_rel_count,
            "total_count": total_result,
            "summary_table": summary_table,
        }
