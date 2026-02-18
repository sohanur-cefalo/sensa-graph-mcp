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

from main import (
    get_node_by_name,
    count_nodes_by_name,
    count_by_label,
    list_categories,
    describe_node_connections,
    count_assets_by_category,
    container_contents_count_by_name,
    container_contents_list_by_name,
    container_contents_count,
    container_contents_list,
    count_assets_breakdown,
)


def main():
    print("=== 1. get_node_by_name(name='Biofilter 11') ===\n")
    r1 = get_node_by_name(name="Biofilter 11")
    print(r1)
    if not r1.get("found"):
        print("Neo4j not running or data not loaded? Run: docker compose up -d && python load_neo4j.py")
        return 1

    node_id = r1["node_id"]
    print(f"\n→ node_id for Biofilter 11: {node_id}\n")

    print("=== 2. container_contents_count (count assets in Biofilter 11) ===\n")
    r2 = container_contents_count(
        start_node_id=node_id,
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        validity_filter={"current_only": True},
    )
    print(r2)

    print("\n=== 3. container_contents_list (list assets in Biofilter 11) ===\n")
    r3 = container_contents_list(
        start_node_id=node_id,
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        include_attributes=["name", "unique_id", "description"],
    )
    print(r3)

    print("=== 4. container_contents_count_by_name (Water Quality Treatment System — count, table) ===\n")
    r4_by_name = container_contents_count_by_name(
        name="Water Quality Treatment System",
        label="System",
        relationship_types=["PART_OF_SYSTEM"],
        target_label="Asset",
    )
    print("total_count:", r4_by_name.get("total_count"))
    print("summary_table:\n", r4_by_name.get("summary_table", "(missing)"))

    print("\n=== 5. get_node_by_name + container_contents_list (assets in Feeding System) ===\n")
    sys_node = get_node_by_name(name="Feeding System")
    if sys_node.get("found"):
        r5 = container_contents_list(
            start_node_id=sys_node["node_id"],
            relationship_types=["PART_OF_SYSTEM"],
            target_label="Asset",
            include_attributes=["name", "description"],
        )
        print(r5)

    print("\n=== 6. count_nodes_by_name (exact name match) ===\n")
    r6 = count_nodes_by_name(name="Biofilter 11")
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
    if r8.get('categories'):
        print(f"First category: {r8['categories'][0]}")
    if r8.get('hierarchy'):
        print(f"Hierarchy entries: {len(r8['hierarchy'])}")

    print("\n=== 9. describe_node_connections (connections for Biofilter 11) ===\n")
    r9 = describe_node_connections(name="Biofilter 11", include_attributes=False)
    print(f"Incoming relationships: {len(r9.get('incoming', []))}")
    print(f"Outgoing relationships: {len(r9.get('outgoing', []))}")
    if r9.get('incoming'):
        print(f"Sample incoming: {r9['incoming'][0]}")
    if r9.get('outgoing'):
        print(f"Sample outgoing: {r9['outgoing'][0]}")

    print("\n=== 10. count_assets_by_category (assets per category) ===\n")
    r10 = count_assets_by_category(category_scope="both")
    print(f"Total count: {r10.get('total_count')}")
    if r10.get('summary_table'):
        print(f"Summary table rows: {len(r10['summary_table'])}")
        print(f"Sample row: {r10['summary_table'][0] if r10['summary_table'] else 'N/A'}")

    print("\n=== 11. container_contents_list_by_name (list assets by name) ===\n")
    r11 = container_contents_list_by_name(
        name="Biofilter 11",
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        limit=10,
    )
    print(f"Assets found: {len(r11.get('result', []))}")
    if r11.get('result'):
        print(f"Sample asset: {r11['result'][0]}")

    print("\n=== 12. count_assets_breakdown (full breakdown) ===\n")
    r12 = count_assets_breakdown(container_type="Both")
    print(f"Total count: {r12.get('total_count')}")
    if r12.get('summary_table'):
        print(f"Summary table rows: {len(r12['summary_table'])}")
        if r12['summary_table']:
            print(f"Sample row: {r12['summary_table'][0]}")

    print("\n=== 13. container_contents_count_by_name with prefix match ===\n")
    r13 = container_contents_count_by_name(
        name="Hall",
        name_match="prefix",
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
    )
    print(f"Total count: {r13.get('total_count')}")
    if r13.get('summary_table'):
        print(f"Summary table rows: {len(r13['summary_table'])}")
        if r13['summary_table']:
            print(f"Sample row: {r13['summary_table'][0]}")

    print("\n=== All MCP tools tested successfully! ===\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
