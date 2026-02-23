"""
Explore InfluxDB schema: list tables, fields, and sample data.
"""

import os
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3

load_dotenv()


def explore_schema(database: str = "Clean"):
    """
    Explore the schema of an InfluxDB database.
    
    Args:
        database: Database name (default: "Clean")
    """
    host = os.getenv("INFLUXDB_HOST")
    token = os.getenv("INFLUXDB_TOKEN")
    
    if not host or not token:
        print("❌ Error: INFLUXDB_HOST and INFLUXDB_TOKEN must be set in .env file")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 Exploring InfluxDB Database: {database}")
    print(f"🔗 Host: {host}")
    print(f"{'='*80}\n")
    
    try:
        # Create client
        client = InfluxDBClient3(
            token=token,
            host=host,
            database=database,
        )
        
        # 1. List all tables (measurements)
        print("📋 Available Tables:")
        print("-" * 80)
        
        tables_query = """
        SELECT DISTINCT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'iox'
        ORDER BY table_name
        """
        
        table_results = client.query(query=tables_query, language="sql")
        
        tables = []
        if table_results.num_rows > 0:
            for i in range(table_results.num_rows):
                table_name = table_results["table_name"][i].as_py()
                tables.append(table_name)
                print(f"  • {table_name}")
        else:
            print("  No tables found")
        
        print(f"\n📊 Total tables: {len(tables)}\n")
        
        # 2. For each table, show its schema
        for table in tables[:5]:  # Show first 5 tables to avoid overwhelming output
            print(f"\n{'─'*80}")
            print(f"📝 Table: {table}")
            print(f"{'─'*80}")
            
            # Get column information
            columns_query = f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'iox' AND table_name = '{table}'
            ORDER BY column_name
            """
            
            try:
                columns_results = client.query(query=columns_query, language="sql")
                
                if columns_results.num_rows > 0:
                    print("\n  Columns:")
                    for i in range(columns_results.num_rows):
                        col_name = columns_results["column_name"][i].as_py()
                        col_type = columns_results["data_type"][i].as_py()
                        print(f"    - {col_name:<30} ({col_type})")
                    
                    # Get sample data
                    sample_query = f"SELECT * FROM {table} LIMIT 3"
                    sample_results = client.query(query=sample_query, language="sql")
                    
                    if sample_results.num_rows > 0:
                        print(f"\n  Sample Data ({sample_results.num_rows} rows):")
                        column_names = [field.name for field in sample_results.schema]
                        
                        # Print header
                        print("    " + " | ".join([f"{col[:20]:20}" for col in column_names[:5]]))
                        print("    " + "-" * 70)
                        
                        # Print rows
                        for i in range(min(3, sample_results.num_rows)):
                            row_values = []
                            for col_name in column_names[:5]:
                                val = sample_results[col_name][i].as_py()
                                val_str = str(val)[:20] if val is not None else "NULL"
                                row_values.append(f"{val_str:20}")
                            print("    " + " | ".join(row_values))
                    
                    # Get row count
                    count_query = f"SELECT COUNT(*) as count FROM {table}"
                    count_results = client.query(query=count_query, language="sql")
                    
                    if count_results.num_rows > 0:
                        total_rows = count_results["count"][0].as_py()
                        print(f"\n  Total rows: {total_rows:,}")
                
            except Exception as e:
                print(f"  ⚠️  Error querying table: {str(e)}")
        
        if len(tables) > 5:
            print(f"\n... and {len(tables) - 5} more tables")
        
        print(f"\n{'='*80}")
        print("✅ Schema exploration complete!")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n❌ Error connecting to InfluxDB: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    # Get database from command line or use default
    database = sys.argv[1] if len(sys.argv) > 1 else "Clean"
    
    print("\n🔍 InfluxDB Schema Explorer")
    print(f"   Database: {database}")
    
    explore_schema(database)
    
    print("\n💡 Tips:")
    print("   - Run with different database: python explore_influxdb_schema.py Raw")
    print("   - Modify the script to explore specific tables in detail")
    print()
