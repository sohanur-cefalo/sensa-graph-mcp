"""
Neo4j connection and env config for the Asset Graph.
"""
import os
from typing import Optional

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_CONNECTION_TIMEOUT = float(os.getenv("NEO4J_CONNECTION_TIMEOUT", "15"))

ALLOWED_AGGREGATIONS = frozenset({"count", "list", "sum", "avg", "min", "max"})

_driver = None
_allowed_labels: Optional[frozenset] = None
_get_node_by_name_labels: Optional[tuple] = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            connection_timeout=NEO4J_CONNECTION_TIMEOUT,
        )
    return _driver


def get_all_labels_from_db() -> frozenset:
    """Fetch all node labels from the Neo4j database."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
        return frozenset(labels)


def get_allowed_labels() -> frozenset:
    """Get all allowed node labels (cached)."""
    global _allowed_labels
    if _allowed_labels is None:
        _allowed_labels = get_all_labels_from_db()
    return _allowed_labels


def get_node_by_name_labels() -> tuple:
    """
    Get the priority order of labels for node lookup.
    Excludes MeasuringUnit and Signal from lookup.
    Places Category at the end as it's lowest priority.
    Returns labels in the order they should be searched.
    """
    global _get_node_by_name_labels
    if _get_node_by_name_labels is None:
        all_labels = get_allowed_labels()
        # Define labels that should be excluded from lookup entirely
        excluded_labels = {"MeasuringUnit", "Signal"}
        # Define labels that should be searched last
        low_priority = {"Category"}
        
        # Get primary labels (all except excluded and low priority)
        primary_labels = sorted(all_labels - excluded_labels - low_priority)
        
        # Add low priority labels at the end
        low_priority_sorted = sorted(all_labels & low_priority)
        
        _get_node_by_name_labels = tuple(primary_labels + low_priority_sorted)
    return _get_node_by_name_labels
