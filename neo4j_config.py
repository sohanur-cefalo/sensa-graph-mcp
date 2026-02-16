"""
Neo4j connection and env config for the Asset Graph.
"""
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_CONNECTION_TIMEOUT = float(os.getenv("NEO4J_CONNECTION_TIMEOUT", "15"))

ALLOWED_LABELS = frozenset({"Category", "Location", "System", "MeasuringUnit", "Asset", "Signal"})
GET_NODE_LABEL = "Location"
ALLOWED_AGGREGATIONS = frozenset({"count", "list", "sum", "avg", "min", "max"})

_driver = None


def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            connection_timeout=NEO4J_CONNECTION_TIMEOUT,
        )
    return _driver
