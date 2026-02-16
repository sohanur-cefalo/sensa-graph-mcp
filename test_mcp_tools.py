#!/usr/bin/env python3
"""
Test script: call the MCP tools directly (no LLM, no MCP transport).
Run after: docker compose up -d && python load_neo4j.py
"""
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from neo4j_rag_mcp import get_node_by_name, aggregate_incoming


def main():
    print("=== 1. get_node_by_name(label='Location', name='Biofilter 11') ===\n")
    r1 = get_node_by_name(label="Location", name="Biofilter 11")
    print(r1)
    if not r1.get("found"):
        print("Neo4j not running or data not loaded? Run: docker compose up -d && python load_neo4j.py")
        return 1

    node_id = r1["node_id"]
    print(f"\n→ node_id for Biofilter 11: {node_id}\n")

    print("=== 2. aggregate_incoming (count assets in Biofilter 11) ===\n")
    r2 = aggregate_incoming(
        start_node_id=node_id,
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        aggregation="count",
        validity_filter={"current_only": True},
    )
    print(r2)

    print("\n=== 3. aggregate_incoming (list assets in Biofilter 11) ===\n")
    r3 = aggregate_incoming(
        start_node_id=node_id,
        relationship_types=["LOCATED_IN"],
        target_label="Asset",
        aggregation="list",
        include_attributes=["name", "unique_id", "description"],
    )
    print(r3)

    print("\n=== 4. get_node_by_name + list (assets in Feeding System) ===\n")
    sys_node = get_node_by_name(label="System", name="Feeding System")
    if sys_node.get("found"):
        r4 = aggregate_incoming(
            start_node_id=sys_node["node_id"],
            relationship_types=["PART_OF_SYSTEM"],
            target_label="Asset",
            aggregation="list",
            include_attributes=["name", "description"],
        )
        print(r4)

    return 0


if __name__ == "__main__":
    sys.exit(main())
