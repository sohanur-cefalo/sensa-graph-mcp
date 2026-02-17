"""
Asset Graph RAG — main MCP server entry point.

Neo4j-based RAG MCP server for the Asset Graph. All tools live in the tools/ folder.
"""

from fastmcp import FastMCP

from tools.count_assets_breakdown import count_assets_breakdown  # Full breakdown: assets per Location/System + total (table)
from tools.container_contents_count import container_contents_count  # Count items in one node (by node_id from get_node_by_name)
from tools.container_contents_count_by_name import container_contents_count_by_name  # "How many assets in Biofilter 11?" (by name, exact/prefix)
from tools.container_contents_list import container_contents_list  # List items in one node (by node_id)
from tools.container_contents_list_by_name import container_contents_list_by_name  # "List assets in X" / "What's in X?" (by name)
from tools.count_by_label import count_by_label  # Global count: "Total assets in the graph?", "How many Locations?"
from tools.count_nodes_by_name import count_nodes_by_name  # Existence/count by name: "Do we have any X?", "How many named X?"
from tools.get_node_by_name import get_node_by_name  # Find one node by name (Location→System→Asset); get node_id for count/list tools

# -----------------------------------------------------------------------------
# MCP instructions
# -----------------------------------------------------------------------------

MCP_INSTRUCTIONS: str = (
    "Query the asset knowledge graph (Neo4j) via MCP tools for natural language QA. "
    "Count in container by name: container_contents_count_by_name(name, relationship_types=['LOCATED_IN'], target_label='Asset') — finds nodes with that name, counts incoming assets per node, returns summary_table and total_count. "
    "List in container by name: container_contents_list_by_name(name, ...) for full lists. "
    "For systems use label='System' and relationship_types=['PART_OF_SYSTEM']. "
    "For partial names (e.g. all Biofilter 1, 2, ...) use name_match='prefix'. "
    "To restrict to a parent location use parent_location_name='Hall 1' or 'RAS'. "
    "Single node by ID: get_node_by_name(name) then container_contents_count(start_node_id, ...) or container_contents_list(start_node_id, ...). "
    "Existence: count_nodes_by_name(name). Global count: count_by_label(label). "
    "Full graph breakdown: count_assets_breakdown(container_type='Both') — returns summary_table and total_count; always show total first then the table. "
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
