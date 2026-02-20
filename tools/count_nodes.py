"""Count nodes with a given name (optionally by label)."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import get_allowed_labels, get_driver, get_node_by_name_labels


def count_nodes(
    name: str,
    label: Optional[str] = None,
) -> dict[str, Any]:
    """
    Count nodes with the given name. Use for existence/count questions like
    "Do we have any X?" or "How many X are there?". If label is not set,
    counts across all available node types in priority order.
    Returns total count and per-label breakdown.
    """
    allowed_labels = get_allowed_labels()
    if label is not None and label not in allowed_labels:
        return {"error": f"label must be one of {sorted(allowed_labels)} or null"}
    labels_to_count = [label] if label else list(get_node_by_name_labels())
    driver = get_driver()
    with driver.session() as session:
        total = 0
        by_label: dict[str, int] = {}
        for lbl in labels_to_count:
            query = (
                f"MATCH (n:{lbl}) WHERE toLower(n.name) = toLower($name) "
                "RETURN count(n) AS c"
            )
            result = session.run(query, name=name)
            row = result.single()
            c = row["c"] if row else 0
            by_label[lbl] = c
            total += c
        return {
            "name": name,
            "total_count": total,
            "by_label": by_label,
            "found": total > 0,
        }
