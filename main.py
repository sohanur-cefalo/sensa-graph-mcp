"""
Asset Graph RAG — main MCP server entry point.

Neo4j-based RAG MCP server for the Asset Graph. All tools live in the tools/ folder.
"""

from fastmcp import FastMCP

from tools.count_assets_breakdown import count_assets_breakdown  # Full breakdown: assets per Location/System + total (table)
from tools.count_assets_by_category import count_assets_by_category  # Asset count per category (location + system categories)
from tools.container_contents_count import container_contents_count  # Count items in one node (by node_id from get_node_by_name)
from tools.container_contents_count_by_name import container_contents_count_by_name  # "How many assets in Biofilter 11?" (by name, exact/prefix)
from tools.container_contents_list import container_contents_list  # List items in one node (by node_id)
from tools.container_contents_list_by_name import container_contents_list_by_name  # "List assets in X" / "What's in X?" (by name)
from tools.count_by_label import count_by_label  # Global count: "Total assets in the graph?", "How many Locations?"
from tools.count_nodes_by_name import count_nodes_by_name  # Existence/count by name: "Do we have any X?", "How many named X?"
from tools.describe_node_connections import describe_node_connections  # How a node is connected (in/out relationships)
from tools.get_node_by_name import get_node_by_name  # Find one node by name (Location→System→Asset→Category); get node_id for count/list tools
from tools.get_schema import get_schema  # Introspect labels, relationship types, property keys (fallback)
from tools.list_categories import list_categories  # Category nodes and BELONGS_TO hierarchy (Site, Plant, System, SubSystem, etc.)
from tools.read_cypher import read_cypher  # Execute read-only Cypher (fallback when domain tools are insufficient)

# -----------------------------------------------------------------------------
# MCP instructions
# -----------------------------------------------------------------------------

MCP_INSTRUCTIONS: str = (
    "Query the asset knowledge graph (Neo4j) via MCP tools for natural language QA. "
    "Use list_categories() to discover all available categories and their hierarchy (BELONGS_TO relationships). "
    "Asset count per category: count_assets_by_category(category_scope='both') for assets per location and system categories. "
    "Connection details: describe_node_connections(name) — for any node returns incoming and outgoing relationships (type + other node name/label). Use for 'How is X connected?', 'What is inside X?', 'How are nodes connected?'. "
    "Count in container by name: container_contents_count_by_name(name, relationship_types=['LOCATED_IN'], target_label='Asset') — counts incoming assets per node. "
    "IMPORTANT for partial/generic queries like 'How many Halls?' or 'Halls in facility X': ALWAYS use container_contents_count_by_name with name_match='prefix' to find all matching nodes (e.g., Hall 1, Hall 2). "
    "List in container by name: container_contents_list_by_name(name, ...). Specify appropriate relationship_types and label based on your use case. "
    "For partial names or when looking for multiple numbered items (Hall 1, Hall 2, etc.) use name_match='prefix'. For exact matches use name_match='exact' (default). parent_location_name restricts to a parent location. "
    "Single node: get_node_by_name(name) — looks up nodes by name across all available node types; then use container_contents_count(start_node_id, ...) or container_contents_list(start_node_id, ...). "
    "Existence: count_nodes_by_name(name) checks for EXACT name matches only. For prefix/partial matching, use container_contents_count_by_name or container_contents_list_by_name with name_match='prefix'. Global count: count_by_label(label). "
    "Full breakdown: count_assets_breakdown(container_type='Both') and count_assets_by_category(category_scope='both'). "
    "When presenting count results: show total_count first, then display the summary_table as-is. "
    "Fallback: get_schema() for graph structure (labels, relationship types, property keys); read_cypher(query, limit?) for read-only Cypher when domain tools cannot answer. Database is read-only."
)

# -----------------------------------------------------------------------------
# MCP app and tool registration
# -----------------------------------------------------------------------------

mcp = FastMCP(
    "Asset Graph RAG",
    instructions=MCP_INSTRUCTIONS,
)

mcp.tool()(get_node_by_name)
mcp.tool()(count_nodes_by_name)
mcp.tool()(count_by_label)
mcp.tool()(list_categories)
mcp.tool()(describe_node_connections)
mcp.tool()(count_assets_by_category)
mcp.tool()(container_contents_count_by_name)
mcp.tool()(container_contents_list_by_name)
mcp.tool()(container_contents_count)
mcp.tool()(container_contents_list)
mcp.tool()(count_assets_breakdown)
mcp.tool()(get_schema)
mcp.tool()(read_cypher)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def run() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
