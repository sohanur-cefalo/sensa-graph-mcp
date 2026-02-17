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
        "Count/list in location by name: use aggregate_incoming_by_name(name, relationship_types=['LOCATED_IN'], target_label='Asset', aggregation='count'|'list') — finds ALL nodes with that name, then for EACH node counts/lists incoming assets and returns per-node breakdown plus total. "
        "For a partial name (e.g. 'Biofilter' meaning all Biofilter 1, Biofilter 2, Biofilter 11, ...), use name_match='prefix' so names that START WITH the given string are included, then counts are aggregated across all matches. "
        "To restrict to a parent (e.g. 'assets in Biofilter in Hall 1' or 'in Biofilter under RAS'): set parent_location_name='Hall 1' or parent_location_name='RAS' — only Location nodes that are transitively under that parent via LOCATED_IN are considered. "
        "Single-node flow: get_node_by_name(name) then aggregate_incoming(node_id, ...) — get_node_by_name returns only the first match. "
        "Existence ('Do we have any X?'): count_nodes_by_name(name). "
        "Global count ('How many Assets in total?'): count_by_label(label). "
        "List with full details: aggregate_incoming(..., aggregation='list', include_attributes=None). "
        "When presenting count results from aggregate_incoming_by_name: always show the total first (e.g. 'There are N items (assets) in [LocationName] in total.'), then if there are multiple locations with that name, say 'That's across M locations named [LocationName]:', then a table with columns 'Location (fingerprint)' and 'Assets', one row per location (use the fingerprint field from each per_node entry), and a final 'Total' row with the total count. Always use this format for location asset counts."
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
    Returns only the first matching node. For all nodes with this name and their asset counts, use aggregate_incoming_by_name.
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


def _name_where_condition(mode: Literal["exact", "prefix"]) -> str:
    """Return Cypher WHERE condition for name match. Uses $name parameter."""
    if mode == "prefix":
        return "toLower(n.name) STARTS WITH toLower($name)"
    return "toLower(n.name) = toLower($name)"


@mcp.tool()
def aggregate_incoming_by_name(
    name: str,
    relationship_types: list[str],
    aggregation: Literal["count", "list"],
    target_label: Optional[str] = None,
    label: Optional[str] = None,
    name_match: Literal["exact", "prefix"] = "exact",
    parent_location_name: Optional[str] = None,
    validity_filter: Optional[dict] = None,
    limit: int = 1000,
) -> dict[str, Any]:
    """
    Find ALL nodes matching the given name (Location first, then Asset), then for EACH such node
    run the same logic as aggregate_incoming: count or list nodes that have INCOMING relationships
    of the given types to that node. Use for questions like "How many assets in Biofilter 11?"
    (exact) or "How many items in Biofilter?" (prefix: matches Biofilter 1, Biofilter 2, ...).
    name_match: "exact" = full name match; "prefix" = names that start with name (e.g. Biofilter -> Biofilter 1, Biofilter 2, Biofilter 11). Returns per-node breakdown and total.
    label: restrict name lookup to this label (default: try Location then Asset).
    parent_location_name: if set, only consider Location nodes that are (transitively) under this
    parent via outgoing LOCATED_IN (e.g. "Hall 1" or "RAS"). Use for "assets in Biofilter in Hall 1".
    When presenting count results: show total first, then if multiple locations exist, a table with
    columns "Location (fingerprint)" and "Assets" (use per_node[].fingerprint and per_node[].result), and a Total row. Always use this format.
    """
    if aggregation not in ("count", "list"):
        return {"error": "aggregation must be 'count' or 'list' for aggregate_incoming_by_name"}
    if target_label is not None and target_label not in ALLOWED_LABELS:
        return {"error": f"target_label must be one of {sorted(ALLOWED_LABELS)}"}
    if label is not None and label not in ALLOWED_LABELS:
        return {"error": f"label must be one of {sorted(ALLOWED_LABELS)} or null"}

    validity_filter = validity_filter or {}
    current_only = validity_filter.get("current_only", True)
    as_of_date = validity_filter.get("as_of_date")
    validity_clause = ""
    if current_only and not as_of_date:
        validity_clause = " AND (r.validity_to IS NULL OR r.validity_to = '')"
    elif as_of_date:
        validity_clause = (
            " AND r.validity_from <= datetime($as_of_date) "
            "AND (r.validity_to IS NULL OR r.validity_to >= datetime($as_of_date))"
        )

    labels_to_try = [label] if label else list(GET_NODE_BY_NAME_LABELS)
    rel_types = "|".join(relationship_types) if relationship_types else []
    if not rel_types:
        return {"error": "relationship_types cannot be empty"}
    target_label_clause = f":{target_label}" if target_label else ""

    name_cond = _name_where_condition(name_match)
    # Only Location nodes can be filtered by parent (Location->Location LOCATED_IN hierarchy)
    parent_clause = ""
    parent_params: dict = {}
    if parent_location_name:
        parent_clause = " AND EXISTS { (n)-[:LOCATED_IN*]->(parent:Location) WHERE toLower(parent.name) = toLower($parent_name) }"
        parent_params = {"parent_name": parent_location_name}

    driver = get_driver()
    with driver.session() as session:
        # 1) Find all nodes matching name (exact or prefix), optionally under parent_location_name
        start_nodes: list[dict] = []
        for lbl in labels_to_try:
            # Apply parent filter only to Location (hierarchy is Location LOCATED_IN Location)
            use_parent = parent_location_name and lbl == "Location"
            q = f"MATCH (n:{lbl}) WHERE {name_cond}{parent_clause if use_parent else ''} RETURN n"
            params = {"name": name, **parent_params} if use_parent else {"name": name}
            result = session.run(q, params)
            for record in result:
                out = _node_to_dict(record)
                out["label"] = lbl
                start_nodes.append(out)
        if not start_nodes:
            return {
                "name": name,
                "found": False,
                "nodes": [],
                "per_node": [],
                "total_result": 0,
                "total_relationship_count": 0,
            }

        params: dict = {"limit": limit}
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

            if aggregation == "count":
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
            else:
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
                        nodes.append(d)
                attrs = node_info.get("attributes") or {}
                per_node.append({
                    "node_id": node_id,
                    "label": node_info.get("label"),
                    "fingerprint": attrs.get("fingerprint"),
                    "attributes": attrs,
                    "result": nodes,
                    "relationship_count": len(nodes),
                })
                total_result += len(nodes)
                total_rel_count += len(nodes)

        return {
            "name": name,
            "found": True,
            "nodes_count": len(start_nodes),
            "per_node": per_node,
            "total_result": total_result,
            "total_relationship_count": total_rel_count,
        }


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
