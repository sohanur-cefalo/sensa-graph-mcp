"""Count nodes with a given name (optionally by label)."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import ALLOWED_LABELS, get_driver

from tools._shared import GET_NODE_BY_NAME_LABELS


def count_nodes_by_name(
    name: str,
    label: Optional[str] = None,
) -> dict[str, Any]:
    """
    Count nodes with the given name. Use for existence/count questions like
    "Do we have any Acidity?" or "How many X are there?". If label is not set,
    counts across Location, System, and Asset (same order as get_node_by_name).
    Returns total count and per-label breakdown.
    """
    if label is not None and label not in ALLOWED_LABELS:
        return {"error": f"label must be one of {sorted(ALLOWED_LABELS)} or null"}
    labels_to_count = [label] if label else list(GET_NODE_BY_NAME_LABELS)
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
