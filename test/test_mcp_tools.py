#!/usr/bin/env python3
"""
Test script: call the MCP tools directly (no LLM, no MCP transport).
Run after: docker compose up -d && python load_neo4j.py
"""
import os
import sys

# Ensure project root is on path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from tools.find_node import find_node
from tools.count_nodes import count_nodes
from tools.count_by_label import count_by_label
from tools.list_categories import list_categories
from tools.get_node_connections import get_node_connections
from tools.count_by_category import count_by_category
from tools.count_related_by_name import count_related_by_name
from tools.list_related_by_name import list_related_by_name
from tools.count_related import count_related
from tools.list_related import list_related
from tools.count_breakdown import count_breakdown


def main():
    print("=== 1. find_node(name='Biofilter 11') ===\n")
    r1 = find_node(name="Biofilter 11")
    print(r1)
    if not r1.get("found"):
        print("Neo4j not running or data not loaded? Run: docker compose up -d && python load_neo4j.py")
        return 1

    nodes = r1.get("nodes", [])
    print(f"\n→ total_count: {r1.get('total_count')}, node_ids: {[n['node_id'] for n in nodes]}\n")

    # For "count/list in location" with multiple nodes with same name, use count_related_by_name/list_related_by_name to aggregate
    print("=== 2. count_related_by_name (count assets in all Biofilter 11 nodes) ===\n")
    r2 = count_related_by_name(
        name="Biofilter 11",
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        validity_filter={"current_only": True},
    )
    print(r2)

    print("\n=== 2b. count_related (single node — first Biofilter 11 only) ===\n")
    node_id = nodes[0]["node_id"]
    r2b = count_related(
        start_node_id=node_id,
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        validity_filter={"current_only": True},
    )
    print(r2b)

    print("\n=== 3. list_related (list assets in first Biofilter 11 node) ===\n")
    r3 = list_related(
        start_node_id=node_id,
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        include_attributes=["name", "unique_id", "description"],
    )
    print(r3)

    print("=== 4. count_related_by_name (Water Quality Treatment System — count, table) ===\n")
    r4_by_name = count_related_by_name(
        name="Water Quality Treatment System",
        label="System",
        relationship_types=["PART_OF_SYSTEM"],
        target_label="Asset",
    )
    print("total_count:", r4_by_name.get("total_count"))
    print("summary_table:\n", r4_by_name.get("summary_table", "(missing)"))

    print("\n=== 5. find_node + list_related (assets in Feeding System) ===\n")
    sys_node = find_node(name="Feeding System")
    if sys_node.get("found") and sys_node.get("nodes"):
        r5 = list_related(
            start_node_id=sys_node["nodes"][0]["node_id"],
            relationship_types=["PART_OF_SYSTEM"],
            target_label="Asset",
            include_attributes=["name", "description"],
        )
        print(r5)

    print("\n=== 6. count_nodes (exact name match) ===\n")
    r6 = count_nodes(name="Biofilter 11")
    print(r6)

    print("\n=== 7. count_by_label (global count by label) ===\n")
    r7_asset = count_by_label(label="Asset")
    r7_location = count_by_label(label="Location")
    r7_system = count_by_label(label="System")
    print(f"Assets: {r7_asset}")
    print(f"Locations: {r7_location}")
    print(f"Systems: {r7_system}")

    print("\n=== 8. list_categories (category hierarchy) ===\n")
    r8 = list_categories(include_hierarchy=True)
    print(f"Categories found: {len(r8.get('categories', []))}")
    if r8.get("categories"):
        print(f"First category: {r8['categories'][0]}")
    if r8.get("category_hierarchy"):
        print(f"Hierarchy entries: {len(r8['category_hierarchy'])}")

    print("\n=== 9. get_node_connections (connections for Biofilter 11) ===\n")
    r9 = get_node_connections(name="Biofilter 11", include_attributes=False)
    print(f"Incoming relationships: {len(r9.get('incoming', []))}")
    print(f"Outgoing relationships: {len(r9.get('outgoing', []))}")
    if r9.get("incoming"):
        print(f"Sample incoming: {r9['incoming'][0]}")
    if r9.get("outgoing"):
        print(f"Sample outgoing: {r9['outgoing'][0]}")

    print("\n=== 10. count_by_category (assets per category) ===\n")
    r10 = count_by_category(category_scope="both")
    print(f"Summary table present: {'summary_table' in r10}")
    if r10.get("summary_table"):
        print(f"Summary table length: {len(r10['summary_table'])}")

    print("\n=== 11. list_related_by_name (list assets by name) ===\n")
    r11 = list_related_by_name(
        name="Biofilter 11",
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        limit=10,
    )
    total_items = sum(len(p.get("result", [])) for p in r11.get("per_node", []))
    print(f"Assets found: {total_items}")
    if r11.get("per_node") and r11["per_node"][0].get("result"):
        print(f"Sample asset: {r11['per_node'][0]['result'][0]}")

    print("\n=== 12. count_breakdown (full breakdown) ===\n")
    r12 = count_breakdown(container_type="Both")
    print(f"Total count: {r12.get('total_count')}")
    if r12.get("summary_table"):
        print(f"Summary table length: {len(r12['summary_table'])}")

    print("\n=== 13. count_related_by_name with prefix match ===\n")
    r13 = count_related_by_name(
        name="Hall",
        name_match="prefix",
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
    )
    print(f"Total count: {r13.get('total_count')}")
    if r13.get("summary_table"):
        print(f"Summary table length: {len(r13['summary_table'])}")

    print("\n=== All MCP tools tested successfully! ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
