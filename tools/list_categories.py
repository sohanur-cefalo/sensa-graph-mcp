"""List Category nodes and how they connect (BELONGS_TO hierarchy)."""

from __future__ import annotations

from typing import Any

from neo4j_config import get_driver


def list_categories(include_hierarchy: bool = True) -> dict[str, Any]:
    """
    List all Category nodes and optionally how they connect to each other via BELONGS_TO.
    Use for: "What categories exist?", "How are categories connected?",
    "What is the category hierarchy?".
    """
    driver = get_driver()
    with driver.session() as session:
        # All category nodes
        q_cats = """
        MATCH (c:Category)
        RETURN c.name AS name, c.fingerprint AS fingerprint, elementId(c) AS node_id
        ORDER BY c.name
        """
        result = session.run(q_cats)
        categories = [
            {"name": r["name"], "fingerprint": r["fingerprint"], "node_id": r["node_id"]}
            for r in result
        ]

        out: dict[str, Any] = {
            "categories": categories,
            "category_count": len(categories),
        }

        if include_hierarchy:
            # BELONGS_TO between Category nodes (e.g. SubSystem -> System, Plant -> Site)
            q_rel = """
            MATCH (from:Category)-[r:BELONGS_TO]->(to:Category)
            RETURN from.name AS from_name, from.fingerprint AS from_fingerprint,
                   to.name AS to_name, to.fingerprint AS to_fingerprint,
                   type(r) AS relationship_type
            ORDER BY from.name, to.name
            """
            result = session.run(q_rel)
            hierarchy = [
                {
                    "from_category": r["from_name"],
                    "to_category": r["to_name"],
                    "relationship_type": r["relationship_type"],
                    "description": f"{r['from_name']} --BELONGS_TO--> {r['to_name']}",
                }
                for r in result
            ]
            out["category_hierarchy"] = hierarchy
            out["hierarchy_description"] = (
                "Category hierarchy (BELONGS_TO): "
                + "; ".join(h["description"] for h in hierarchy)
                if hierarchy
                else "No BELONGS_TO links between categories."
            )

    return out
