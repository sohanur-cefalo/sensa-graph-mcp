"""Full graph asset breakdown: assets per Location and/or System in table form."""

from __future__ import annotations

from typing import Any, Literal, Optional

from neo4j_config import get_driver

from tools._shared import build_validity_clause, format_count_summary_table

_BREAKDOWN_CONFIG: dict[str, tuple[str, str]] = {
    "Location": ("LOCATED_IN", "Location"),
    "System": ("PART_OF_SYSTEM", "System"),
    "Context": ("LOCATED_IN", "Context"),
}


def count_assets_breakdown(
    container_type: Literal["Location", "System", "Context", "Both"] = "Both",
    validity_filter: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    For "how many assets in my graph" / full breakdown: list every Location, System, and/or Context
    with how many assets each has. Returns summary_table(s) and total_count so the answer is
    always in table format with a total row.
    container_type: "Location", "System", "Context" (assets per context/location hierarchy),
    or "Both" (Location + System). Use "Context" when the graph uses Context nodes for places.
    """
    validity_clause, as_of_date = build_validity_clause(validity_filter)
    optional_validity = f" AND (r IS NULL OR (1=1 {validity_clause}))" if validity_clause else ""

    types_to_run: list[Literal["Location", "System", "Context"]] = (
        ["Location", "System", "Context"] if container_type == "Both" else [container_type]
    )
    params: dict[str, Any] = {}
    if as_of_date:
        params["as_of_date"] = as_of_date

    driver = get_driver()
    out: dict[str, Any] = {
        "total_assets_in_graph": 0,
        "breakdown": {},
        "summary_tables": {},
        "per_container": {},
    }

    with driver.session() as session:
        for dim in types_to_run:
            rel_type, container_label = _BREAKDOWN_CONFIG[dim]
            query = f"""
            MATCH (container:{container_label})
            OPTIONAL MATCH (a:Asset)-[r:{rel_type}]->(container)
            WHERE 1=1 {optional_validity}
            WITH container, count(a) AS cnt
            RETURN container.fingerprint AS fingerprint, elementId(container) AS node_id,
                   container.name AS name, cnt
            ORDER BY container.fingerprint
            """
            result = session.run(query, params)
            per_node: list[dict[str, Any]] = []
            total = 0
            for record in result:
                fp = record.get("fingerprint") or "(no fingerprint)"
                node_id = record.get("node_id")
                name = record.get("name")
                cnt = record.get("cnt") or 0
                total += cnt
                per_node.append({
                    "node_id": node_id,
                    "label": container_label,
                    "fingerprint": fp,
                    "name": name,
                    "result": cnt,
                    "relationship_count": cnt,
                })
            table = format_count_summary_table(
                per_node, total, container_label=container_label, count_column="Assets"
            )
            out["breakdown"][dim] = {"per_node": per_node, "total_result": total}
            out["summary_tables"][dim] = table
            out["per_container"][dim] = per_node
            out["total_assets_in_graph"] = out.get("total_assets_in_graph", 0) + total

    if container_type == "Both" and types_to_run:
        totals = [
            out["breakdown"].get(d, {}).get("total_result", 0)
            for d in types_to_run
        ]
        non_zero = [t for t in totals if t]
        out["total_assets_in_graph"] = max(totals) if non_zero else 0

    out["total_count"] = out["total_assets_in_graph"]
    if container_type == "Both":
        parts = [
            f"**By {dim}**\n\n" + out["summary_tables"].get(dim, "")
            for dim in types_to_run
        ]
        out["summary_table"] = "\n\n".join(parts)
    else:
        out["summary_table"] = out["summary_tables"].get(container_type, "")

    return out
