import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class Neo4jIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ingest(self, data):
        with self.driver.session() as session:
            # 0. Create Constraint/Index for performance
            print("Ensuring uniqueness constraints...")
            labels_to_constrain = ["Category", "Context", "Asset", "Location", "System"]
            for label in labels_to_constrain:
                try:
                    session.run(f"CREATE CONSTRAINT {label.lower()}_unique_id_unique IF NOT EXISTS FOR (n:{label}) REQUIRE n.unique_id IS UNIQUE")
                except Exception as e:
                    print(f"Warning: Could not create constraint for {label}: {e}")
            
            # 1. Ingest Nodes
            print(f"Ingesting {len(data['nodes'])} nodes...")
            for node in data['nodes']:
                labels_list = node['labels']
                labels_str = ":".join(labels_list)
                props = node['properties']
                
                # All nodes now use unique_id (GUID) as identity
                query = f"""
                MERGE (n:{labels_str} {{unique_id: $unique_id}})
                SET n += $properties
                """
                session.run(query, unique_id=props['unique_id'], properties=props)

            # 2. Ingest Relationships
            print(f"Ingesting {len(data['relationships'])} relationships...")
            for rel in data['relationships']:
                from_uid = rel['from_unique_id']
                to_uid = rel['to_unique_id']
                rel_type = rel['type']
                rel_props = rel.get('properties', {})
                
                query = f"""
                MATCH (a {{unique_id: $from_uid}})
                MATCH (b {{unique_id: $to_uid}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += $properties
                """
                session.run(query, from_uid=from_uid, to_uid=to_uid, properties=rel_props)


def main():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    data_file = "data/neo4j_data.json"
    
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found.")
        return

    with open(data_file, 'r') as f:
        data = json.load(f)

    ingestor = Neo4jIngestor(uri, user, password)
    try:
        ingestor.ingest(data)
        print("Ingestion completed successfully.")
    except Exception as e:
        print(f"An error occurred during ingestion: {e}")
    finally:
        ingestor.close()

if __name__ == "__main__":
    main()
