"""Introspect Neo4j graph schema: labels, relationship types, and property keys."""

from __future__ import annotations

from typing import Any

from neo4j_config import get_driver


def get_schema() -> dict[str, Any]:
    """
    Return the structural schema of the Neo4j graph: node labels, relationship types,
    and property keys. Use when you need to understand the graph structure to write
    Cypher or when domain tools do not cover the question.
    """
    driver = get_driver()
    with driver.session() as session:
        labels: list[str] = []
        result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
        labels = [r["label"] for r in result]

        rel_types: list[str] = []
        result = session.run(
            "CALL db.relationshipTypes() YIELD relationshipType "
            "RETURN relationshipType ORDER BY relationshipType"
        )
        rel_types = [r["relationshipType"] for r in result]

        property_keys: list[str] = []
        try:
            result = session.run(
                "CALL db.propertyKeys() YIELD propertyKey "
                "RETURN propertyKey ORDER BY propertyKey"
            )
            property_keys = [r["propertyKey"] for r in result]
        except Exception:
            # Older Neo4j or no db.propertyKeys; leave empty
            property_keys = []

    return {
        "labels": labels,
        "relationship_types": rel_types,
        "property_keys": property_keys,
        "summary": (
            f"Labels ({len(labels)}): {', '.join(labels)}. "
            f"Relationship types ({len(rel_types)}): {', '.join(rel_types)}. "
            f"Property keys ({len(property_keys)}): {', '.join(property_keys[:20])}"
            + ("..." if len(property_keys) > 20 else "")
        ),
    }
