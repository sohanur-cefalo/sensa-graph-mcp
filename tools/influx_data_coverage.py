"""
Report InfluxDB data coverage: time period and which signals (uuid) have data per table.

Run from project root with venv Python:
  env/bin/python tools/influx_data_coverage.py

Or:  PYTHONPATH=. env/bin/python tools/influx_data_coverage.py
"""

import os
import sys

# Allow running from repo root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from dotenv import load_dotenv

load_dotenv()

from tools.influx_client import execute_query


# Known tables if information_schema is not available
CLEAN_TABLES = ["pi_agent_clean_min_v1", "pi_agent_clean_hour_v1", "pi_agent_clean_day_v1"]
RAW_TABLES = ["pi_agent_min_v1"]


def get_tables_from_schema(database: str) -> list[str]:
    """List table names from InfluxDB information_schema if available."""
    try:
        q = """
        SELECT DISTINCT table_name
        FROM information_schema.tables
        WHERE table_schema = 'iox'
        ORDER BY table_name
        """
        rows = execute_query(database, q)
        if rows:
            return [r.get("table_name") for r in rows if r.get("table_name")]
    except Exception:
        pass
    return CLEAN_TABLES if database == "Clean" else RAW_TABLES


def get_time_bounds(database: str, table: str) -> dict | None:
    """Get min(time), max(time), count(*) for a table."""
    try:
        q = f"""
        SELECT
          min(time) AS min_time,
          max(time) AS max_time,
          count(*) AS row_count
        FROM {table}
        """
        rows = execute_query(database, q)
        if rows and len(rows) > 0:
            return rows[0]
    except Exception as e:
        return {"error": str(e)}
    return None


def get_distinct_uuids(database: str, table: str, limit: int = 500) -> list[str]:
    """Get distinct uuid values that have data in the table (sample)."""
    try:
        q = f"""
        SELECT DISTINCT uuid
        FROM {table}
        LIMIT {limit}
        """
        rows = execute_query(database, q)
        if rows:
            return [r.get("uuid") for r in rows if r.get("uuid")]
    except Exception:
        pass
    return []


def main():
    print("\n" + "=" * 70)
    print("InfluxDB data coverage: time period and signals per table")
    print("=" * 70)

    host = os.getenv("INFLUXDB_HOST")
    if not host:
        print("\nError: INFLUXDB_HOST not set in .env")
        sys.exit(1)
    print(f"\nHost: {host}\n")

    for database in ["Clean", "Raw"]:
        print("-" * 70)
        print(f"Database: {database}")
        print("-" * 70)

        try:
            tables = get_tables_from_schema(database)
        except Exception as e:
            print(f"  Could not list tables: {e}")
            tables = CLEAN_TABLES if database == "Clean" else RAW_TABLES

        for table in tables:
            bounds = get_time_bounds(database, table)
            if bounds is None:
                print(f"\n  Table: {table}")
                print("    No data or unable to query.")
                continue

            err = bounds.get("error")
            if err:
                print(f"\n  Table: {table}")
                print(f"    Error: {err}")
                continue

            min_t = bounds.get("min_time")
            max_t = bounds.get("max_time")
            count = bounds.get("row_count", 0)

            print(f"\n  Table: {table}")
            print(f"    Rows:      {count:,}")
            if min_t and max_t:
                print(f"    Min time:  {min_t}")
                print(f"    Max time:  {max_t}")
                uuids = get_distinct_uuids(database, table, limit=50)
                if uuids:
                    print(f"    Signals (uuid) with data: {len(uuids)} (showing up to 50)")
                    for u in uuids[:10]:
                        print(f"      - {u}")
                    if len(uuids) > 10:
                        print(f"      ... and {len(uuids) - 10} more")
            else:
                print("    No rows (empty table).")

    print("\n" + "=" * 70)
    print("How to query and get results:")
    print("  - Use a time range that falls between Min time and Max time above.")
    print("  - Example (last 7 days): time_range='7 days' or natural_query='last 7 days'")
    print("  - If data is old, use a wider range, e.g. time_range='90 days' or '365 days'.")
    print("  - Locations with signals in the graph: Hall 1, Hall 2, Hall 3, Hall 4, etc.")
    print("  - Signal names: Flow, Capacity, Ozone (and others per location).")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
