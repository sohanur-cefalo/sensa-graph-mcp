"""Shared helpers and constants for MCP tools."""

from __future__ import annotations

from typing import Any, Literal, Optional

from neo4j_config import ALLOWED_LABELS, get_driver

# Lookup order: Location, System, Asset, then Category (so "01_WMS" matches System node before Category "System")
GET_NODE_BY_NAME_LABELS: tuple[str, ...] = ("Location", "System", "Asset", "Category")


def node_to_dict(record: Any, node_var: str = "n") -> dict[str, Any]:
    """Convert a Neo4j record node to a dict with node_id, label, attributes."""
    node = record.get(node_var)
    if node is None:
        return {}
    props = dict(node)
    node_id = getattr(node, "element_id", None) or node.id
    return {
        "node_id": str(node_id),
        "label": next(iter(node.labels), ""),
        "attributes": props,
    }


def name_where_condition(mode: Literal["exact", "prefix"]) -> str:
    """Return Cypher WHERE condition for name match. Uses $name parameter."""
    if mode == "prefix":
        return "toLower(n.name) STARTS WITH toLower($name)"
    return "toLower(n.name) = toLower($name)"


def format_count_summary_table(
    per_node: list[dict[str, Any]],
    total_result: int,
    container_label: str = "Container",
    count_column: str = "Count",
) -> str:
    """Build a markdown table: one row per node (fingerprint + count), then a Total row."""
    if not per_node:
        return f"| {container_label} (fingerprint) | {count_column} |\n| --- | --- |\n| *(none)* | 0 |\n| **Total** | **0** |"
    header = f"| {container_label} (fingerprint) | {count_column} |"
    sep = "| --- | --- |"
    rows = []
    for p in per_node:
        fp = p.get("fingerprint") or p.get("attributes", {}).get("fingerprint") or "(no fingerprint)"
        cnt = p.get("result", 0)
        rows.append(f"| {fp} | {cnt} |")
    rows.append(f"| **Total** | **{total_result}** |")
    return "\n".join([header, sep] + rows)


def build_validity_clause(
    validity_filter: Optional[dict[str, Any]],
    rel_var: str = "r",
) -> tuple[str, Optional[str]]:
    """Return (validity_clause, as_of_date). rel_var is the relationship variable name in the query."""
    validity_filter = validity_filter or {}
    current_only = validity_filter.get("current_only", True)
    as_of_date = validity_filter.get("as_of_date")
    if current_only and not as_of_date:
        clause = f" AND ({rel_var}.validity_to IS NULL OR {rel_var}.validity_to = '')"
    elif as_of_date:
        clause = (
            f" AND {rel_var}.validity_from <= datetime($as_of_date) "
            f"AND ({rel_var}.validity_to IS NULL OR {rel_var}.validity_to >= datetime($as_of_date))"
        )
    else:
        clause = ""
    return clause, as_of_date
