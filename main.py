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
from tools.list_categories import list_categories  # Category nodes and BELONGS_TO hierarchy (Site, Plant, System, SubSystem, etc.)

# -----------------------------------------------------------------------------
# MCP instructions
# -----------------------------------------------------------------------------

MCP_INSTRUCTIONS: str = (
    "Query the asset knowledge graph (Neo4j) via MCP tools for natural language QA. "
    "Entry point: Aardal is a Location connected to Site (Category) via BELONGS_TO_LOCATION_CATEGORY. "
    "Categories: System, SubSystem, Site, Plant, Section, SubSection (and others). Use list_categories() to list all and how they connect (BELONGS_TO hierarchy). "
    "Asset count per category: count_assets_by_category(category_scope='both') for assets per location category (Site/Plant/Section/SubSection) and per system category (System/SubSystem). "
    "Connection details: describe_node_connections(name) — for any node (Location, System, Asset, Category) returns incoming and outgoing relationships (type + other node name/label). Use for 'How is system X connected?', 'What is inside X?', 'How are systems connected?'. "
    "Count in container by name: container_contents_count_by_name(name, relationship_types=['LOCATED_IN'], target_label='Asset') — counts incoming assets per node. "
    "List in container by name: container_contents_list_by_name(name, ...). For systems use label='System' and relationship_types=['PART_OF_SYSTEM']. "
    "For partial names use name_match='prefix'. parent_location_name restricts to a parent location. "
    "Single node: get_node_by_name(name) — looks up Location, then System, then Asset, then Category; then container_contents_count(start_node_id, ...) or container_contents_list(start_node_id, ...). "
    "Existence: count_nodes_by_name(name). Global count: count_by_label(label). "
    "Full breakdown: count_assets_breakdown(container_type='Both') and count_assets_by_category(category_scope='both'). "
    "When presenting count results: show total_count first, then display the summary_table as-is."
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


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def run() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
