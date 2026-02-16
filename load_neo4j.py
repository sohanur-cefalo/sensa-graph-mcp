#!/usr/bin/env python3
"""
Load neo4j_dummy_data.json into a Neo4j database.
Uses NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD from environment or .env.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def load_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def load_json(data_path: Path) -> dict:
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")


def create_indexes(tx):
    for label in ["Category", "Location", "System", "MeasuringUnit", "Asset", "Signal"]:
        try:
            tx.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.unique_id)")
        except Exception:
            pass  # Index may already exist


def create_node(tx, node: dict):
    labels = node.get("labels", [])
    if not labels:
        return
    label_str = ":".join(labels)
    props = {k: v for k, v in node.items() if k != "labels" and v is not None}
    placeholders = ", ".join(f"n.{k} = ${k}" for k in props)
    query = f"""
    MERGE (n:{label_str} {{unique_id: $unique_id}})
    SET n += $props
    """
    tx.run(query, unique_id=node["unique_id"], props=props)


def create_relationship(tx, rel: dict):
    # Relationship type must be literal in Cypher; source is our JSON so safe
    rel_type = rel["type"].replace(" ", "_").replace("-", "_")
    validity_to = rel.get("validity_to")
    if validity_to:
        query = f"""
        MATCH (a {{unique_id: $from_id}}), (b {{unique_id: $to_id}})
        CREATE (a)-[r:{rel_type} {{
            validity_from: datetime($validity_from),
            validity_to: datetime($validity_to)
        }}]->(b)
        """
    else:
        query = f"""
        MATCH (a {{unique_id: $from_id}}), (b {{unique_id: $to_id}})
        CREATE (a)-[r:{rel_type} {{
            validity_from: datetime($validity_from)
        }}]->(b)
        """
    params = {
        "from_id": rel["from_unique_id"],
        "to_id": rel["to_unique_id"],
        "validity_from": rel.get("validity_from", "2024-01-01T00:00:00Z"),
    }
    if validity_to:
        params["validity_to"] = validity_to
    tx.run(query, params)


def main():
    data_path = Path(__file__).parent / "neo4j_dummy_data.json"
    if not data_path.exists():
        print(f"Missing {data_path}")
        return 1

    data = load_json(data_path)
    driver = load_driver()

    try:
        with driver.session() as session:
            print("Clearing existing graph...")
            session.execute_write(clear_graph)
            print("Creating nodes...")
            for node in data["nodes"]:
                session.execute_write(create_node, node)
            print("Creating relationships...")
            for rel in data["relationships"]:
                session.execute_write(create_relationship, rel)
            print("Creating indexes on unique_id...")
            session.execute_write(create_indexes)
        print("Done. Nodes:", len(data["nodes"]), "Relationships:", len(data["relationships"]))
    finally:
        driver.close()

    return 0


if __name__ == "__main__":
    exit(main())
