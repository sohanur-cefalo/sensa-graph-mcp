#!/usr/bin/env python3
"""
Test dynamic label and category discovery.
"""
import os
import sys

# Ensure project root is on path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from neo4j_config import get_allowed_labels, get_node_by_name_labels
from tools.list_categories import list_categories
from tools.count_by_category import count_by_category


def main():
    print("=== 1. Dynamic Label Discovery ===\n")
    allowed = get_allowed_labels()
    print(f"All labels in database: {sorted(allowed)}")
    
    lookup_order = get_node_by_name_labels()
    print(f"Node lookup priority order: {lookup_order}\n")
    
    print("=== 2. List Taxonomy (Dynamic) ===\n")
    categories = list_categories(include_hierarchy=True)
    print(f"Total categories: {categories.get('category_count')}")
    print(f"Category names: {[c['name'] for c in categories.get('categories', [])]}")
    if categories.get('category_hierarchy'):
        print(f"\nCategory hierarchy connections: {len(categories['category_hierarchy'])}")
        for h in categories['category_hierarchy'][:3]:  # Show first 3
            print(f"  - {h['description']}")
    print()
    
    print("=== 3. Count by Category (Dynamic Discovery) ===\n")
    asset_counts = count_by_category(category_scope="both")
    print(f"Total assets (location categories): {asset_counts.get('total_assets_location_categories')}")
    print(f"Location categories found: {[c['category_name'] for c in asset_counts.get('by_location_category', [])]}")
    print(f"\nTotal assets (system categories): {asset_counts.get('total_assets_system_categories')}")
    print(f"System categories found: {[c['category_name'] for c in asset_counts.get('by_system_category', [])]}")
    
    print("\n=== Summary Tables ===")
    print(asset_counts.get('summary_table', '(none)'))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
