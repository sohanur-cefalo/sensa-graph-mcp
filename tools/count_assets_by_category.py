"""Asset count per category (location categories and system categories)."""

from __future__ import annotations

from typing import Any, Literal, Optional

from neo4j_config import get_driver

from tools._shared import build_validity_clause

# Location categories: assets are counted via Location -[:BELONGS_TO_LOCATION_CATEGORY]-> Category
LOCATION_CATEGORY_NAMES = ("Site", "Plant", "Section", "SubSection")
# System categories: assets are counted via System -[:BELONG_TO_SYSTEM_CATEGORY]-> Category
SYSTEM_CATEGORY_NAMES = ("System", "SubSystem")


def count_assets_by_category(
    category_scope: Literal["location", "system", "both"] = "both",
    validity_filter: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Count assets per category. Use for "How many assets per Site/Plant/Section/SubSection?"
    (location categories) and "How many assets per System/SubSystem category?" (system categories).
    - location: only location categories (Site, Plant, Section, SubSection) — assets in locations
      that BELONGS_TO_LOCATION_CATEGORY that category.
    - system: only system categories (System, SubSystem) — assets in systems that
      BELONG_TO_SYSTEM_CATEGORY that category.
    - both: both location and system category breakdowns.
    """
    validity_loc, as_of_date = build_validity_clause(validity_filter, rel_var="r_in")
    validity_sys, _ = build_validity_clause(validity_filter, rel_var="r_part")
    params: dict[str, Any] = {}
    if as_of_date:
        params["as_of_date"] = as_of_date
    optional_validity = f" AND (r_in IS NULL OR (1=1 {validity_loc}))" if validity_loc else ""
    optional_validity_sys = f" AND (r_part IS NULL OR (1=1 {validity_sys}))" if validity_sys else ""

    driver = get_driver()
    out: dict[str, Any] = {
        "by_location_category": [],
        "by_system_category": [],
        "summary_tables": {},
        "total_assets_location_categories": 0,
        "total_assets_system_categories": 0,
    }

    with driver.session() as session:
        if category_scope in ("location", "both"):
            # Per location category: count assets in locations that belong to this category
            q_loc = f"""
            MATCH (cat:Category) WHERE cat.name IN $loc_names
            OPTIONAL MATCH (loc:Location)-[r_loc:BELONGS_TO_LOCATION_CATEGORY]->(cat)
            OPTIONAL MATCH (a:Asset)-[r_in:LOCATED_IN]->(loc)
            WHERE 1=1 {optional_validity}
            WITH cat.name AS category_name, cat.fingerprint AS category_fingerprint,
                 count(DISTINCT a) AS asset_count, count(DISTINCT loc) AS location_count
            RETURN category_name, category_fingerprint, asset_count, location_count
            ORDER BY category_name
            """
            result = session.run(
                q_loc,
                {"loc_names": list(LOCATION_CATEGORY_NAMES), **params},
            )
            rows = list(result)
            for r in rows:
                out["by_location_category"].append({
                    "category_name": r["category_name"],
                    "category_fingerprint": r["category_fingerprint"],
                    "asset_count": r["asset_count"] or 0,
                    "location_count": r["location_count"] or 0,
                })
            out["total_assets_location_categories"] = sum(
                x["asset_count"] for x in out["by_location_category"]
            )
            # Summary table
            lines = ["| Category | Asset count | Location count |", "| --- | --- | --- |"]
            for row in out["by_location_category"]:
                lines.append(
                    f"| {row['category_name']} | {row['asset_count']} | {row['location_count']} |"
                )
            lines.append(
                f"| **Total (location categories)** | **{out['total_assets_location_categories']}** | — |"
            )
            out["summary_tables"]["location_categories"] = "\n".join(lines)

        if category_scope in ("system", "both"):
            # Per system category: count assets in systems that belong to this category
            q_sys = f"""
            MATCH (cat:Category) WHERE cat.name IN $sys_names
            OPTIONAL MATCH (sys:System)-[r_sys:BELONG_TO_SYSTEM_CATEGORY]->(cat)
            OPTIONAL MATCH (a:Asset)-[r_part:PART_OF_SYSTEM]->(sys)
            WHERE 1=1 {optional_validity_sys}
            WITH cat.name AS category_name, cat.fingerprint AS category_fingerprint,
                 count(DISTINCT a) AS asset_count, count(DISTINCT sys) AS system_count
            RETURN category_name, category_fingerprint, asset_count, system_count
            ORDER BY category_name
            """
            result = session.run(
                q_sys,
                {"sys_names": list(SYSTEM_CATEGORY_NAMES), **params},
            )
            rows = list(result)
            for r in rows:
                out["by_system_category"].append({
                    "category_name": r["category_name"],
                    "category_fingerprint": r["category_fingerprint"],
                    "asset_count": r["asset_count"] or 0,
                    "system_count": r["system_count"] or 0,
                })
            out["total_assets_system_categories"] = sum(
                x["asset_count"] for x in out["by_system_category"]
            )
            lines = ["| Category | Asset count | System count |", "| --- | --- | --- |"]
            for row in out["by_system_category"]:
                lines.append(
                    f"| {row['category_name']} | {row['asset_count']} | {row['system_count']} |"
                )
            lines.append(
                f"| **Total (system categories)** | **{out['total_assets_system_categories']}** | — |"
            )
            out["summary_tables"]["system_categories"] = "\n".join(lines)

    if category_scope == "both":
        out["summary_table"] = (
            "**By location category**\n\n" + out["summary_tables"].get("location_categories", "")
            + "\n\n**By system category**\n\n" + out["summary_tables"].get("system_categories", "")
        )
    else:
        key = "location_categories" if category_scope == "location" else "system_categories"
        out["summary_table"] = out["summary_tables"].get(key, "")

    return out
