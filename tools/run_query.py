"""Execute read-only query (e.g. Cypher). Rejects writes, schema changes, and PROFILE/EXPLAIN."""

from __future__ import annotations

import re
from typing import Any

from neo4j_config import get_driver


# Forbidden Cypher keywords (read-only: no writes, schema, or profiling)
_READ_ONLY_FORBIDDEN = re.compile(
    r"\b("
    r"CREATE|MERGE|DELETE|SET|REMOVE|DROP|DETACH|"
    r"EXPLAIN|PROFILE|"
    r"START\s+DATABASE|STOP\s+DATABASE|"
    r"CREATE\s+INDEX|CREATE\s+CONSTRAINT|DROP\s+INDEX|DROP\s+CONSTRAINT"
    r")\b",
    re.IGNORECASE,
)


def run_query(query: str, limit: int = 1000) -> dict[str, Any]:
    """
    Execute a read-only query (e.g. Cypher). Use when domain tools are not sufficient.
    Only SELECT-style queries are allowed (MATCH, RETURN, etc.).
    Write operations, schema changes, and PROFILE/EXPLAIN are rejected.
    """
    query = (query or "").strip()
    if not query:
        return {"error": "Query cannot be empty"}

    if _READ_ONLY_FORBIDDEN.search(query):
        return {
            "error": "Read-only mode: query must not contain write or admin operations "
            "(e.g. CREATE, MERGE, DELETE, SET, REMOVE, DROP, DETACH, EXPLAIN, PROFILE, "
            "or schema operations). Use only MATCH, RETURN, WITH, OPTIONAL MATCH, etc."
        }

    driver = get_driver()
    try:
        with driver.session() as session:
            normalized = query.rstrip().rstrip(";")
            if " LIMIT " not in normalized.upper():
                normalized = f"{normalized} LIMIT {limit}"
            result = session.run(normalized)
            records = [dict(r) for r in result]
        return {"result": records, "count": len(records)}
    except Exception as e:
        return {"error": str(e), "result": [], "count": 0}
