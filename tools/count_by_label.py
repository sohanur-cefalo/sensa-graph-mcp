"""Count all nodes with a given label."""

from __future__ import annotations

from typing import Any

from neo4j_config import ALLOWED_LABELS, get_driver


def count_by_label(label: str) -> dict[str, Any]:
    """
    Count all nodes with the given label. Use for global count questions like
    "How many Location entities are there in total?" or
    "What is the total number of Assets?".
    """
    if label not in ALLOWED_LABELS:
        return {"error": f"label must be one of {sorted(ALLOWED_LABELS)}"}
    driver = get_driver()
    with driver.session() as session:
        query = f"MATCH (n:{label}) RETURN count(n) AS total"
        result = session.run(query)
        row = result.single()
        total = row["total"] if row else 0
    return {"label": label, "total_count": total}
