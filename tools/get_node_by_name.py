"""Find a node by name (Location, then System, then Asset)."""

from __future__ import annotations

from typing import Any, Optional

from neo4j_config import get_driver

from tools._shared import GET_NODE_BY_NAME_LABELS, node_to_dict


def get_node_by_name(
    name: str,
    include_attributes: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Find a node by its name attribute. Looks up Location first, then System, then Asset if not found.
    Use this first to get node_id for container_contents_count or container_contents_list.
    For existence/count questions like "Do we have any Acidity?", prefer count_nodes_by_name.
    Returns only the first matching node. For all nodes with this name and their asset counts,
    use container_contents_count_by_name or container_contents_list_by_name.
    """
    driver = get_driver()
    with driver.session() as session:
        for lbl in GET_NODE_BY_NAME_LABELS:
            query = (
                f"MATCH (n:{lbl}) WHERE toLower(n.name) = toLower($name) "
                "RETURN n LIMIT 1"
            )
            result = session.run(query, name=name)
            record = result.single()
            if record:
                out = node_to_dict(record)
                if include_attributes and out.get("attributes"):
                    out["attributes"] = {
                        k: out["attributes"][k]
                        for k in include_attributes
                        if k in out["attributes"]
                    }
                out["found"] = True
                return out
        return {"found": False, "node_id": None, "label": None, "attributes": None}
