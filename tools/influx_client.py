"""
InfluxDB connection manager for querying time-series data.
Provides a singleton client instance for efficient connection reuse.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3

load_dotenv()

# Cache clients by database name
_client_cache: dict[str, InfluxDBClient3] = {}


def get_influx_client(database: str) -> InfluxDBClient3:
    """
    Get or create an InfluxDB client instance for the specified database.
    
    Args:
        database: Database name (e.g., "Raw", "Clean")
        
    Returns:
        InfluxDBClient3 instance configured for the database
    """
    global _client_cache
    
    # Return cached client if available
    if database in _client_cache:
        return _client_cache[database]
    
    host = os.getenv("INFLUXDB_HOST")
    token = os.getenv("INFLUXDB_TOKEN")
    
    if not host or not token:
        raise ValueError(
            "INFLUXDB_HOST and INFLUXDB_TOKEN must be set in environment variables"
        )
    
    # Create a new client for each database (InfluxDB 3.0 uses database in connection)
    client = InfluxDBClient3(
        token=token,
        host=host,
        database=database,
    )
    
    # Cache the client
    _client_cache[database] = client
    
    return client


def execute_query(database: str, query: str) -> list[dict]:
    """
    Execute an InfluxDB SQL query and return results as a list of dictionaries.
    
    Args:
        database: Database name (e.g., "Raw", "Clean")
        query: SQL query string
        
    Returns:
        List of dictionaries, each representing a row with column names as keys
        
    Raises:
        Exception: If query execution fails
    """
    client = get_influx_client(database)
    
    try:
        # Execute query and get PyArrow table directly
        table = client.query(query=query, language="sql")
        
        # Convert to list of dictionaries
        if table.num_rows == 0:
            return []
        
        # Get column names from schema
        column_names = [field.name for field in table.schema]
        
        # Convert PyArrow table to list of dicts
        results = []
        for i in range(table.num_rows):
            row = {}
            for col_name in column_names:
                col = table[col_name]
                # PyArrow scalars have as_py() method to convert to Python types
                try:
                    value = col[i].as_py() if hasattr(col[i], 'as_py') else col[i]
                except AttributeError:
                    # Fallback for non-scalar types
                    value = str(col[i])
                row[col_name] = value
            results.append(row)
        
        return results
    except Exception as e:
        raise Exception(f"InfluxDB query failed: {str(e)}")
