#!/usr/bin/env python3
"""
Reset the knowledge graph by deleting all nodes and relationships in Neo4j.
Uses NEO4J_URI, NEO4J_USER/NEO4J_USERNAME, NEO4J_PASSWORD from environment or .env.
"""
import os
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def clear_graph(tx):
    result = tx.run("MATCH (n) DETACH DELETE n")
    summary = result.consume()
    return getattr(summary.counters, "nodes_deleted", None)


def reset(driver):
    with driver.session() as session:
        return session.execute_write(clear_graph)


def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        print("Resetting knowledge graph (deleting all nodes and relationships)...")
        deleted = reset(driver)
        if deleted is not None:
            print(f"Done. Deleted {deleted} nodes (and all their relationships).")
        else:
            print("Done. Graph cleared.")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        driver.close()


if __name__ == "__main__":
    sys.exit(main())
