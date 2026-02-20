"""
Answer evaluation_questions.csv using the same logic as the MCP tools:
  find_node, count_nodes, count_by_label, count_related, list_related

Minimal tool usage:
- Count in location: find_node(X) + count_related(start_node_id, LOCATED_IN, Asset)
- Existence: count_nodes(name)
- Global count: count_by_label(label)
- List in location: find_node(X) + list_related(start_node_id, LOCATED_IN, Asset)

Requires Neo4j with data loaded via ingest_to_neo4j.py.

Note: data/neo4j_data.json currently has only Location->Location LOCATED_IN (hierarchy), not
Asset->Location. So "count items in location" and "list in location" return 0/empty until
Asset-LOCATED_IN-Location edges are present in the graph.
"""
import csv
import os
import re
from typing import Any, Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_node_by_name(driver, label: str, name: str) -> dict[str, Any]:
    """Same contract as MCP find_node (local helper for this script)."""
    with driver.session() as session:
        query = f"MATCH (n:{label} {{name: $name}}) RETURN n LIMIT 1"
        result = session.run(query, name=name)
        record = result.single()
        if not record:
            return {"found": False, "node_id": None}
        node = record["n"]
        node_id = getattr(node, "element_id", None) or node.id
        return {"found": True, "node_id": str(node_id)}


def count_nodes(driver, label: str, name: Optional[str] = None) -> int:
    """Same contract as MCP count_nodes; returns result count."""
    with driver.session() as session:
        if name is None:
            query = f"MATCH (n:{label}) RETURN count(n) AS result"
            result = session.run(query)
        else:
            query = f"MATCH (n:{label} {{name: $name}}) RETURN count(n) AS result"
            result = session.run(query, name=name)
        row = result.single()
        return row["result"] if row else 0


def traverse_count_assets_in_location(driver, location_node_id: str) -> int:
    """Assets that are LOCATED_IN this location (INCOMING LOCATED_IN, target Asset, count)."""
    with driver.session() as session:
        # Accept both NULL and empty string validity_to (per ingested neo4j_data.json)
        query = """
        MATCH (start) WHERE elementId(start) = $start_node_id
        MATCH (target:Asset)-[r:LOCATED_IN]->(start)
        WHERE (r.validity_to IS NULL OR r.validity_to = '')
        RETURN count(target) AS result
        """
        result = session.run(query, start_node_id=location_node_id)
        row = result.single()
        return row["result"] if row else 0


def traverse_list_assets_in_location(driver, location_node_id: str, limit: int = 500) -> list[dict]:
    """List assets in location (INCOMING LOCATED_IN, target Asset, list)."""
    with driver.session() as session:
        query = """
        MATCH (start) WHERE elementId(start) = $start_node_id
        MATCH (target:Asset)-[r:LOCATED_IN]->(start)
        WHERE (r.validity_to IS NULL OR r.validity_to = '')
        RETURN target.name AS name, elementId(target) AS node_id
        LIMIT $limit
        """
        result = session.run(query, start_node_id=location_node_id, limit=limit)
        return [{"name": record["name"], "node_id": record["node_id"]} for record in result]


# ---- Question classification and entity extraction ----

def extract_location_name(question: str, qtype: str) -> Optional[str]:
    """Extract location name from count/list questions."""
    if "Count Items in Location" not in qtype and "Imprecise Listing" not in qtype:
        return None
    # "Count the number of items in Biofilter 11." / "in CenterChannel." / "in Treatment area."
    m = re.search(r"\b(?:in|inside)\s+([^.?,?]+?)[.?]*\s*$", question, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?:in|inside)\s+([^.?,?]+?)(?:\?|,)", question, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def extract_existence_asset_name(question: str) -> Optional[str]:
    """Extract asset type for existence check: 'Are there any Flows?' -> 'Flow'."""
    # "Are there any Flows?" -> Flow; "Do we have any Motor_Current?" -> Motor_Current; "Is there a CO here?" -> CO
    m = re.search(r"(?:any|a)\s+([A-Za-z0-9_]+)\s*\??\s*$", question, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        if name.endswith("s") and not name.endswith("ss") and name not in ("Oxygen", "Ozone", "Redox", "CO"):
            name = name[:-1]  # Flows -> Flow; Temperatures -> Temperature
        return name
    return None


def extract_global_count_label(question: str) -> Optional[str]:
    """Extract label for global count: 'How many Location entities?' -> Location."""
    q = question.lower()
    if "location entities" in q or "location" in q and "total" in q:
        return "Location"
    if "measuringunit" in q or "measuring unit" in q:
        return "MeasuringUnit"
    if "assets" in q or "asset" in q:
        return "Asset"
    if "systems" in q or "system" in q:
        return "System"
    return None


def answer_question(driver, question: str, qtype: str) -> tuple[Any, int]:
    """
    Answer using minimal MCP-like calls. Returns (answer_value, number_of_tool_calls).
    """
    calls = 0

    if "Count Items in Location" in qtype:
        loc = extract_location_name(question, qtype)
        if not loc:
            return None, 0
        node_res = get_node_by_name(driver, "Location", loc)
        calls += 1
        if not node_res.get("found"):
            return 0, calls
        count = traverse_count_assets_in_location(driver, node_res["node_id"])
        calls += 1
        return count, calls

    if "Existence Check" in qtype:
        name = extract_existence_asset_name(question)
        if not name:
            return None, 0
        count = count_nodes(driver, "Asset", name)
        calls += 1
        plural = name + "s"  # Flows, Oxygens, COs, etc. per CSV
        return f"Yes, there are {count} {plural}.", calls

    if "Global Count" in qtype:
        label = extract_global_count_label(question)
        if not label:
            return None, 0
        count = count_nodes(driver, label)
        calls += 1
        return count, calls

    if "Imprecise Listing" in qtype:
        loc = extract_location_name(question, qtype)
        if not loc:
            return None, 0
        node_res = get_node_by_name(driver, "Location", loc)
        calls += 1
        if not node_res.get("found"):
            return [], calls
        items = traverse_list_assets_in_location(driver, node_res["node_id"])
        calls += 1
        return [x["name"] for x in items], calls

    return None, 0


def main():
    csv_path = "evaluation_questions.csv"
    out_path = "evaluation_results.csv"
    if not os.path.exists(csv_path):
        print(f"Missing {csv_path}")
        return

    driver = get_driver()
    results = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        for row in rows:
            question = row.get("Question", "").strip()
            expected = row.get("Probable Answer", "").strip()
            qtype = row.get("Type", "").strip()
            pred, num_calls = answer_question(driver, question, qtype)

            if pred is None and num_calls == 0:
                pred_str = ""
                match = ""
            else:
                if isinstance(pred, list):
                    pred_str = "; ".join(pred) if pred else ""
                else:
                    pred_str = str(pred)
                try:
                    exp_val = int(expected) if expected.isdigit() else expected
                    match = "yes" if pred == exp_val or pred_str == str(expected) else "no"
                except Exception:
                    match = "yes" if pred_str == expected else "no" if expected else ""

            results.append({
                "Question": question,
                "Type": qtype,
                "Expected": expected,
                "Predicted": pred_str,
                "Match": match,
                "ToolCalls": num_calls,
            })

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Question", "Type", "Expected", "Predicted", "Match", "ToolCalls"])
            w.writeheader()
            w.writerows(results)

        matches = sum(1 for r in results if r["Match"] == "yes")
        with_exp = sum(1 for r in results if r["Expected"])
        total_calls = sum(r["ToolCalls"] for r in results)
        print(f"Wrote {out_path}")
        print(f"Questions with expected answer: {with_exp}")
        print(f"Matches: {matches} / {len(results)} (of all) ; {matches} / {with_exp} (of with expected)")
        print(f"Total MCP-like tool calls: {total_calls} (avg {total_calls / len(results):.1f} per question)")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
