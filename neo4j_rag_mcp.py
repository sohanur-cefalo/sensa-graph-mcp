"""
Neo4j-based RAG MCP server for the Asset Graph.
Exposes tools: get_node_by_name, count_nodes_by_name, count_by_label, aggregate_incoming.

All location-based queries (count/list items in X, list equipment in X) use INCOMING only:
  assets that are LOCATED_IN the location = aggregate_incoming(LOCATED_IN, Asset, ...).
No traversal; each tool runs a single Cypher query.
"""
from typing import Any, Literal, Optional

from fastmcp import FastMCP

from neo4j_config import (
    ALLOWED_AGGREGATIONS,
    ALLOWED_LABELS,
    get_driver,
)

# Order of labels to try when resolving a node by name
GET_NODE_BY_NAME_LABELS = ("Location", "Asset")

mcp = FastMCP(
    "Asset Graph RAG",
    instructions=(
        "Query the asset knowledge graph (Neo4j) via generic MCP tools for natural language QA. "
        "Count/list in location: get_node_by_name(Location, name) then aggregate_incoming(LOCATED_IN, Asset, count|list) — incoming only. "
        "Existence ('Do we have any X?'): count_nodes_by_name(name). "
        "Global count ('How many Assets in total?'): count_by_label(label). "
        "List with full details: aggregate_incoming(..., aggregation='list', include_attributes=None)."
    ),
)


def _node_to_dict(record, node_var: str = "n") -> dict:
    node = record.get(node_var)
    if node is None:
        return {}
    props = dict(node)
    node_id = getattr(node, "element_id", None) or node.id
    return {"node_id": str(node_id), "label": next(iter(node.labels), ""), "attributes": props}


@mcp.tool()
def count_nodes_by_name(
    name: str,
    label: Optional[str] = None,
) -> dict[str, Any]:
    """
    Count nodes with the given name. Use for existence/count questions like
    "Do we have any Acidity?" or "How many X are there?". If label is not set,
    counts across Location and Asset (same order as get_node_by_name).
    Returns total count and per-label breakdown.
    """
    if label is not None and label not in ALLOWED_LABELS:
        return {"error": f"label must be one of {sorted(ALLOWED_LABELS)} or null"}
    labels_to_count = [label] if label else list(GET_NODE_BY_NAME_LABELS)
    driver = get_driver()
    with driver.session() as session:
        total = 0
        by_label: dict[str, int] = {}
        for lbl in labels_to_count:
            query = f"MATCH (n:{lbl}) WHERE toLower(n.name) = toLower($name) RETURN count(n) AS c"
            result = session.run(query, name=name)
            row = result.single()
            c = row["c"] if row else 0
            by_label[lbl] = c
            total += c
        return {
            "name": name,
            "total_count": total,
            "by_label": by_label,
            "found": total > 0,
        }


@mcp.tool()
def count_by_label(label: str) -> dict[str, Any]:
    """
    Count all nodes with the given label. Use for global count questions like
    "How many Location entities are there in total?" or "What is the total number of Assets?".
    """
    if label not in ALLOWED_LABELS:
        return {"error": f"label must be one of {sorted(ALLOWED_LABELS)}"}
    driver = get_driver()
    with driver.session() as session:
        query = f"MATCH (n:{label}) RETURN count(n) AS total"
        result = session.run(query)
        row = result.single()
        total = row["total"] if row else 0
    return {"label": label, "total_count": total}


@mcp.tool()
def get_node_by_name(
    name: str,
    include_attributes: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Find a node by its name attribute. Looks up Location first, then Asset if not found.
    Use this first to get node_id for aggregate_incoming.
    For existence/count questions like "Do we have any Acidity?", prefer count_nodes_by_name.
    """
    driver = get_driver()
    with driver.session() as session:
        for label in GET_NODE_BY_NAME_LABELS:
            query = f"MATCH (n:{label}) WHERE toLower(n.name) = toLower($name) RETURN n LIMIT 1"
            result = session.run(query, name=name)
            record = result.single()
            if record:
                out = _node_to_dict(record)
                if include_attributes and out.get("attributes"):
                    out["attributes"] = {k: out["attributes"][k] for k in include_attributes if k in out["attributes"]}
                out["found"] = True
                return out
        return {"found": False, "node_id": None, "label": None, "attributes": None}


@mcp.tool()
def aggregate_incoming(
    start_node_id: str,
    relationship_types: list[str],
    aggregation: Literal["count", "list", "sum", "avg", "min", "max"],
    target_label: Optional[str] = None,
    validity_filter: Optional[dict] = None,
    limit: int = 1000,
    include_attributes: Optional[list[str]] = None,
    property_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run a single Cypher query: match nodes that have INCOMING relationships of the given
    types TO the start node (use node_id from get_node_by_name), then aggregate.
    For "list equipment in X" / "what's inside X" use INCOMING only (this tool).
    E.g. assets LOCATED_IN a location: relationship_types=["LOCATED_IN"], target_label="Asset".
    Use include_attributes=None to return full node details; pass a list to restrict.
    For sum/avg/min/max set property_name to the numeric property.
    """
    if aggregation not in ALLOWED_AGGREGATIONS:
        return {"error": f"aggregation must be one of {sorted(ALLOWED_AGGREGATIONS)}"}
    if target_label is not None and target_label not in ALLOWED_LABELS:
        return {"error": f"target_label must be one of {sorted(ALLOWED_LABELS)}"}

    validity_filter = validity_filter or {}
    current_only = validity_filter.get("current_only", True)
    as_of_date = validity_filter.get("as_of_date")

    rel_types = "|".join(relationship_types) if relationship_types else ""
    if not rel_types:
        return {"error": "relationship_types cannot be empty"}
    target_label_clause = f":{target_label}" if target_label else ""
    pattern = f"(target{target_label_clause})-[r:{rel_types}]->(start)"

    validity_clause = ""
    if current_only and not as_of_date:
        validity_clause = " AND (r.validity_to IS NULL OR r.validity_to = '')"
    elif as_of_date:
        validity_clause = (
            " AND r.validity_from <= datetime($as_of_date) "
            "AND (r.validity_to IS NULL OR r.validity_to >= datetime($as_of_date))"
        )

    match_start = "MATCH (start) WHERE elementId(start) = $start_node_id"
    params: dict = {"start_node_id": start_node_id, "limit": limit}
    if as_of_date:
        params["as_of_date"] = as_of_date

    driver = get_driver()
    with driver.session() as session:
        if aggregation == "count":
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

        if aggregation in ("sum", "avg", "min", "max") and property_name:
            agg_fn = aggregation.upper()
            query = f"""
            {match_start}
            MATCH {pattern}
            WHERE 1=1 {validity_clause} AND target.{property_name} IS NOT NULL
            RETURN {agg_fn}(target.{property_name}) AS result, count(r) AS rel_count
            """
            result = session.run(query, params)
            row = result.single()
            return {
                "result": row["result"] if row else None,
                "relationship_count": row["rel_count"] if row else 0,
                "target_nodes_found": row["rel_count"] if row else 0,
            }

        if aggregation == "list":
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

    return {"error": "Unsupported aggregation or missing property_name for sum/avg/min/max"}


if __name__ == "__main__":
    mcp.run()
