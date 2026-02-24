"""
Knowledge Graph RAG — main MCP server entry point.

Neo4j-based RAG MCP server. Tools use generic names so they work for any knowledge graph.
"""

from fastmcp import FastMCP

from tools.count_breakdown import count_breakdown
from tools.count_by_category import count_by_category
from tools.count_by_label import count_by_label
from tools.count_nodes import count_nodes
from tools.count_related import count_related
from tools.count_related_by_name import count_related_by_name
from tools.find_node import find_node
from tools.get_node_connections import get_node_connections
from tools.get_schema import get_schema
from tools.list_related import list_related
from tools.list_related_by_name import list_related_by_name
from tools.list_categories import list_categories
from tools.query_influxdb import query_influxdb
from tools.run_query import run_query

# -----------------------------------------------------------------------------
# MCP instructions (generic: work for any knowledge graph)
# -----------------------------------------------------------------------------

MCP_INSTRUCTIONS: str = (
    "Query the knowledge graph via MCP tools for natural language QA. "
    "Use list_categories() to discover categories and their hierarchy. "
    "Entity count per category: count_by_category(category_scope='both'). "
    "Connection details: get_node_connections(name) — for any node returns incoming and outgoing relationships. "
    "For count/list entities in a node (e.g. assets in a location): prefer count_related_by_name(name, relationship_types=[...], target_label='Asset') — it finds ALL nodes with that name, counts related entities per node, and returns the total. Use list_related_by_name for listing. For a single known node_id use count_related/list_related. "
    "Existence: count_nodes(name). Global count: count_by_label(label). "
    "Full breakdown: count_breakdown(container_type='Both') and count_by_category(category_scope='both'). "
    "When presenting count results: show total_count first, then display the summary_table as-is. "
    "Fallback: get_schema() for graph structure; run_query(query, limit?) for read-only query when domain tools cannot answer. Database is read-only. "
    "For time-series (flow trend, last N days flow/temperature): use query_influxdb(location_name?, signal_name?, natural_query?, time_range?, limit?). Either location_name or signal_name is required; signal_name matching is case-insensitive (e.g. 'capacity' finds 'Capacity')."
)

# -----------------------------------------------------------------------------
# MCP app and tool registration (generic names)
# -----------------------------------------------------------------------------

mcp = FastMCP(
    "Knowledge Graph RAG",
    instructions=MCP_INSTRUCTIONS,
)

mcp.tool()(find_node)
mcp.tool()(count_nodes)
mcp.tool()(count_by_label)
mcp.tool()(list_categories)
mcp.tool()(get_node_connections)
mcp.tool()(count_by_category)
mcp.tool()(count_related)
mcp.tool()(count_related_by_name)
mcp.tool()(list_related)
mcp.tool()(list_related_by_name)
mcp.tool()(count_breakdown)
mcp.tool()(get_schema)
mcp.tool()(query_influxdb)
mcp.tool()(run_query)


def run() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
