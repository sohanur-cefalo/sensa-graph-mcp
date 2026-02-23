"""
Query time-series data from InfluxDB based on Signal nodes in the graph.

Use this tool when users ask about:
- Time-series trends (e.g., "last 7 days flow trend")
- Current values or recent measurements
- Anomaly detection (e.g., "is there an accident")
- Historical data analysis
- Comparisons over time

The tool will:
1. Find Signal nodes related to the specified location/asset
2. Match Signal guid to InfluxDB uuid
3. Generate appropriate SQL queries
4. Return time-series data with timestamps
"""

from __future__ import annotations

import os
from typing import Any, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from neo4j_config import get_driver

from tools.influx_client import execute_query

load_dotenv()

# Initialize Anthropic client for SQL generation
claude_api_key = os.getenv("CLAUDE_API_KEY")
claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
anthropic = Anthropic(api_key=claude_api_key) if claude_api_key else None


def find_signals_by_location(
    location_name: str,
    signal_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Find Signal nodes related to a location.
    
    Args:
        location_name: Name of the Location/Context node (e.g., "Hall 1")
        signal_name: Optional signal name filter (e.g., "Flow")
        
    Returns:
        List of Signal node dictionaries with properties
    """
    driver = get_driver()
    
    # Build query to find signals in the location
    # Support both Location and Context node types
    # Path: Signal -> SIGNAL_GENERATED_FROM -> Asset -> LOCATED_IN -> Location/Context
    # Also handle nested locations (signals in sub-locations under the main location)
    query = """
    MATCH (s:Signal)-[:SIGNAL_GENERATED_FROM]->(a:Asset)-[:LOCATED_IN]->(l)
    WHERE (l:Location OR l:Context) AND toLower(l.name) = toLower($location_name)
    """
    
    params = {"location_name": location_name}
    
    if signal_name:
        query += " AND toLower(s.name) = toLower($signal_name)"
        params["signal_name"] = signal_name
    
    query += """
    RETURN s.name AS name, 
           s.guid AS guid, 
           s.table AS table, 
           s.field_name_in_db AS field_name_in_db,
           s.database AS database,
           s.unique_id AS unique_id,
           elementId(s) AS node_id,
           a.name AS asset_name
    
    UNION
    
    MATCH (s:Signal)-[:SIGNAL_GENERATED_FROM]->(a:Asset)-[:LOCATED_IN]->(sub)-[:BELONGS_TO_LOCATION*]->(l)
    WHERE (l:Location OR l:Context) AND toLower(l.name) = toLower($location_name)
    """
    
    if signal_name:
        query += " AND toLower(s.name) = toLower($signal_name)"
    
    query += """
    RETURN s.name AS name, 
           s.guid AS guid, 
           s.table AS table, 
           s.field_name_in_db AS field_name_in_db,
           s.database AS database,
           s.unique_id AS unique_id,
           elementId(s) AS node_id,
           a.name AS asset_name
    """
    
    with driver.session() as session:
        result = session.run(query, params)
        signals = []
        for record in result:
            guid = record.get("guid")
            if not guid:
                continue
            signal = {
                "name": record.get("name"),
                "guid": guid,
                "table": record.get("table"),
                "field_name_in_db": record.get("field_name_in_db"),
                "database": record.get("database"),
                "unique_id": record.get("unique_id"),
                "node_id": record.get("node_id"),
                "asset_name": record.get("asset_name"),
            }
            if signal["table"] and signal["field_name_in_db"]:
                signals.append(signal)
        
        return signals


def generate_sql_with_claude(
    natural_query: str,
    signal_metadata: list[dict[str, Any]],
    time_range: Optional[str] = None,
) -> str:
    """
    Use Claude to generate InfluxDB SQL query from natural language.
    
    Args:
        natural_query: Natural language description of what to query
        signal_metadata: List of Signal node metadata dictionaries
        time_range: Optional explicit time range (e.g., "7 days", "24 hours")
        
    Returns:
        SQL query string
    """
    if not anthropic:
        raise ValueError("Claude API key not configured")
    
    if not signal_metadata:
        raise ValueError("No signal metadata provided")
    
    # Build context about available signals
    signals_info = []
    for sig in signal_metadata:
        signals_info.append(
            f"- Signal: {sig['name']}, GUID: {sig['guid']}, "
            f"Table: {sig['table']}, Field: {sig['field_name_in_db']}, "
            f"Database: {sig['database']}"
        )
    
    signals_context = "\n".join(signals_info)
    
    # Prefer Clean database signals if available
    clean_signals = [s for s in signal_metadata if s.get("database") == "Clean"]
    preferred_signals = clean_signals if clean_signals else signal_metadata
    
    # Choose the best signal (prefer hourly aggregation for trends)
    # Priority: clean_hour > clean_min > clean_day > raw
    preferred_signal = None
    for sig in preferred_signals:
        table = sig.get("table", "").lower()
        if "hour" in table:
            preferred_signal = sig
            break
    
    if not preferred_signal:
        preferred_signal = preferred_signals[0]
    
    # Build prompt for Claude
    prompt = f"""You are generating an InfluxDB SQL query based on a natural language request.

Available Signal Information:
{signals_context}

Selected Signal for Query:
- GUID: {preferred_signal['guid']}
- Table: {preferred_signal['table']}
- Field: {preferred_signal['field_name_in_db']}
- Database: {preferred_signal['database']}

User Query: {natural_query}
{"Time Range: " + time_range if time_range else "Time Range: (none - user did not specify; do NOT add a time filter so that the most recent data in the database is returned)"}

Generate an InfluxDB SQL query that:
1. Selects the '{preferred_signal['field_name_in_db']}' field from table '{preferred_signal['table']}'
2. Filters by uuid = '{preferred_signal['guid']}'
3. Applies time filtering ONLY if a time range was specified above; if "(none - ...)" then do NOT add any time condition (no WHERE time ...), so we get the latest data in the DB.
4. Orders results by time ascending, then add LIMIT 1000
5. Includes appropriate aggregations if needed (e.g., for trends use hourly/daily aggregation)

Important:
- Use WHERE uuid = '{preferred_signal['guid']}' to filter to the correct signal
- If time range is specified: use time >= now() - interval 'X days'. If NOT specified: omit time filter entirely.
- Return only the SQL query, no explanations or markdown formatting
- Use standard SQL syntax compatible with InfluxDB 3.0

SQL Query:"""

    try:
        response = anthropic.messages.create(
            model=claude_model,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        
        sql_query = response.content[0].text.strip()
        
        # Remove markdown code blocks if present
        if sql_query.startswith("```"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query
        
        return sql_query
    except Exception as e:
        raise Exception(f"Failed to generate SQL with Claude: {str(e)}")


def query_influxdb(
    location_name: Optional[str] = None,
    signal_name: Optional[str] = None,
    natural_query: Optional[str] = None,
    time_range: Optional[str] = None,
    aggregation: Optional[str] = None,
    limit: int = 1000,
) -> dict[str, Any]:
    """
    Query time-series data from InfluxDB based on Signal nodes in the graph.
    
    This tool finds Signal nodes related to a location, matches their guid to InfluxDB uuid,
    generates SQL queries (with Claude assistance if needed), and executes them.
    
    Args:
        location_name: Name of Location node (e.g., "Hall 1", "Tank Area 1")
        signal_name: Optional signal name filter (e.g., "Flow", "Temperature")
        natural_query: Natural language description of what to query (e.g., "last 7 days trend")
        time_range: Optional explicit time range (e.g., "7 days", "24 hours")
        aggregation: Optional aggregation method (e.g., "hourly", "daily") - currently used as hint
        limit: Maximum number of data points to return (default: 1000)
        
    Returns:
        Dictionary with:
        - signals_queried: List of all signal metadata (one per GUID; includes asset_name when available)
        - sql_query: First SQL query (or all in sql_queries when multiple signals)
        - data_points: Total number of data points returned
        - time_range: Time range of the data
        - data: List of data points; each point includes time, the signal field (e.g. flow), guid, signal_name, and asset_name so multiple series can be distinguished
        - error: Error message if query failed
    """
    if not location_name:
        return {
            "error": "location_name is required",
            "signals_queried": [],
            "data": [],
        }
    
    try:
        # Step 1: Find Signal nodes
        signals = find_signals_by_location(location_name, signal_name)
        
        if not signals:
            return {
                "error": f"No signals found for location '{location_name}'"
                + (f" with signal name '{signal_name}'" if signal_name else ""),
                "signals_queried": [],
                "data": [],
            }
        
        # Step 2: Prefer Clean database; cap number of signals
        clean_signals = [s for s in signals if s.get("database") == "Clean"]
        signals_to_query = clean_signals if clean_signals else signals
        max_signals = 20
        # One entry per guid, pick best table (hourly for trend/days, else first)
        want_hour = natural_query and ("trend" in natural_query.lower() or "days" in natural_query.lower())
        unique_by_guid: dict[str, dict] = {}
        for sig in signals_to_query:
            g = sig.get("guid")
            if not g:
                continue
            if g not in unique_by_guid:
                unique_by_guid[g] = {**sig}
            elif want_hour and "hour" in (sig.get("table") or "").lower():
                unique_by_guid[g] = {**sig}
        # If we want hour and any guid doesn't have hour table yet, try to get it from full list
        if want_hour:
            for g in list(unique_by_guid):
                if "hour" not in (unique_by_guid[g].get("table") or "").lower():
                    for s in signals_to_query:
                        if s.get("guid") == g and "hour" in (s.get("table") or "").lower():
                            unique_by_guid[g] = {**unique_by_guid[g], "table": s["table"]}
                            break
        signals_to_query = list(unique_by_guid.values())[:max_signals]
        
        limit_per_signal = max(100, limit // len(signals_to_query)) if signals_to_query else limit
        
        # Step 3: Build and run query for each signal (same time logic for all)
        time_clause = ""
        order_and_limit = f"ORDER BY time ASC LIMIT {limit_per_signal}"
        if time_range:
            time_clause = f" AND time >= now() - interval '{time_range}'"
        else:
            order_and_limit = f"ORDER BY time DESC LIMIT {limit_per_signal}"
        
        all_data: list[dict] = []
        signals_queried: list[dict] = []
        sql_queries: list[str] = []
        
        for preferred_signal in signals_to_query:
            field = preferred_signal["field_name_in_db"]
            sql_query = f"""
            SELECT time, {field}
            FROM {preferred_signal['table']}
            WHERE uuid = '{preferred_signal['guid']}'
            {time_clause}
            {order_and_limit}
            """
            database = preferred_signal.get("database", "Raw")
            data = execute_query(database, sql_query)
            if not time_range and data:
                data = list(reversed(data))
            if time_range and not data:
                fallback_sql = f"""
                SELECT time, {field}
                FROM {preferred_signal['table']}
                WHERE uuid = '{preferred_signal['guid']}'
                ORDER BY time DESC LIMIT {limit_per_signal}
                """
                data = execute_query(database, fallback_sql)
                if data:
                    data = list(reversed(data))
                    sql_query = fallback_sql.strip()
            for row in data:
                row["guid"] = preferred_signal["guid"]
                row["signal_name"] = preferred_signal.get("name", "Flow")
                row["asset_name"] = preferred_signal.get("asset_name")
            all_data.extend(data)
            signals_queried.append({
                "signal_name": preferred_signal.get("name"),
                "guid": preferred_signal["guid"],
                "asset_name": preferred_signal.get("asset_name"),
                "table": preferred_signal["table"],
                "database": preferred_signal.get("database"),
                "field_name_in_db": preferred_signal["field_name_in_db"],
            })
            sql_queries.append(sql_query.strip())
        
        # Sort combined data by time (then guid) so multiple series are interleaved chronologically
        all_data.sort(key=lambda r: (r.get("time") or "", r.get("guid") or ""))
        data = all_data[:limit]
        
        # Step 4: Time range summary
        time_range_str = "Unknown"
        if data:
            times = [row.get("time") for row in data if row.get("time")]
            if times:
                time_range_str = f"{min(times)} to {max(times)}"
        
        return {
            "signals_queried": signals_queried,
            "sql_query": sql_queries[0] if sql_queries else "",
            "sql_queries": sql_queries if len(sql_queries) > 1 else None,
            "data_points": len(data),
            "time_range": time_range_str,
            "data": data,
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "signals_queried": [],
            "data": [],
        }
