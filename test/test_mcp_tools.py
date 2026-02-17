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
    container_contents_count,
    container_contents_list,
    container_contents_count_by_name,
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
