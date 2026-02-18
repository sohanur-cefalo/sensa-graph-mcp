#!/usr/bin/env python3
"""
Import a Neo4j backup file into the database.
This script:
1. Resets the current database (deletes all nodes and relationships)
2. Stops Neo4j service
3. Restores the backup file
4. Starts Neo4j service again

Uses NEO4J_URI, NEO4J_USER/NEO4J_USERNAME, NEO4J_PASSWORD from environment or .env.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
CONTAINER_NAME = os.getenv("NEO4J_CONTAINER_NAME", "graph-rag-neo4j")


def check_docker_container():
    """Check if Neo4j Docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )
        return CONTAINER_NAME in result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def clear_graph(driver):
    """Clear all nodes and relationships from the database."""
    with driver.session() as session:
        result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
        record = result.single()
        deleted = record["deleted"] if record else 0
        return deleted


def wait_for_neo4j_ready(max_wait=30):
    """Wait for Neo4j to be ready before operations."""
    print("Waiting for Neo4j to be ready...")
    wait_interval = 2
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=5
            )
            driver.verify_connectivity()
            driver.close()
            print("Neo4j is ready!")
            return True
        except Exception:
            time.sleep(wait_interval)
            elapsed += wait_interval
            if elapsed % 4 == 0:  # Print every 4 seconds
                print(f"Waiting for Neo4j... ({elapsed}s)")
    
    return False


def set_database_offline():
    """Set Neo4j database offline (required for restore)."""
    print("Setting Neo4j database offline...")
    
    # First, wait for Neo4j to be ready
    if not wait_for_neo4j_ready():
        print("Warning: Neo4j not ready. Will use alternative restore method.")
        return False
    
    try:
        # Set the database offline using cypher-shell
        offline_cmd = [
            "docker", "exec", CONTAINER_NAME,
            "cypher-shell", "-u", NEO4J_USER, "-p", NEO4J_PASSWORD,
            "STOP DATABASE neo4j;"
        ]
        result = subprocess.run(
            offline_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "offline" in result.stdout.lower():
            print("Database set to offline.")
            time.sleep(2)
            return True
        else:
            print(f"Warning: Could not set database offline: {result.stderr or result.stdout}")
            # Try alternative: stop the container and use volumes
            return False
    except Exception as e:
        print(f"Note: Could not set database offline via Cypher: {e}")
        return False


def set_database_online():
    """Set Neo4j database online."""
    print("Setting Neo4j database online...")
    try:
        online_cmd = [
            "docker", "exec", CONTAINER_NAME,
            "cypher-shell", "-u", NEO4J_USER, "-p", NEO4J_PASSWORD,
            "START DATABASE neo4j;"
        ]
        result = subprocess.run(
            online_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("Database set to online.")
        else:
            print(f"Warning: Could not set database online: {result.stderr}")
        
        # Wait for Neo4j to be ready
        print("Waiting for Neo4j to be ready...")
        max_wait = 60  # Maximum wait time in seconds
        wait_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        while elapsed < max_wait:
            try:
                driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD),
                    connection_timeout=5
                )
                driver.verify_connectivity()
                driver.close()
                print("Neo4j is ready!")
                return True
            except Exception:
                time.sleep(wait_interval)
                elapsed += wait_interval
                print(f"Waiting for Neo4j... ({elapsed}s)")
        
        print("Warning: Neo4j may not be fully ready yet.", file=sys.stderr)
        return True
    except Exception as e:
        print(f"Error setting database online: {e}", file=sys.stderr)
        return False


def restore_with_stopped_container(backup_path):
    """Restore backup by copying into container first, then stopping and restoring."""
    backup_filename = Path(backup_path).name
    backup_path_abs = backup_path.resolve()
    container_backup_path = f"/tmp/{backup_filename}"
    
    # Stop the container first
    print("Stopping container to perform restore...")
    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], check=True, capture_output=True)
        print("Container stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error stopping container: {e}", file=sys.stderr)
        return False
    
    # Get container image
    try:
        inspect_result = subprocess.run(
            ["docker", "inspect", CONTAINER_NAME, "--format", "{{.Config.Image}}"],
            capture_output=True,
            text=True,
            check=True
        )
        image = inspect_result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting container image: {e}", file=sys.stderr)
        subprocess.run(["docker", "start", CONTAINER_NAME], capture_output=True)
        return False
    
    # Run restore in temporary container with volumes-from and bind mount of backup file
    print("Running restore in temporary container...")
    # Use bind mount to make backup file accessible
    restore_cmd = [
        "docker", "run", "--rm",
        "--volumes-from", CONTAINER_NAME,
        "-v", f"{backup_path_abs}:{container_backup_path}:ro",
        "-e", "NEO4J_ACCEPT_LICENSE_AGREEMENT=yes",
        image,
        "neo4j-admin", "database", "restore",
        "--verbose",
        f"--from-path={container_backup_path}",
        "--overwrite-destination=true",
        "neo4j"
    ]
    
    try:
        result = subprocess.run(restore_cmd, capture_output=True, text=True, check=True)
        print("Backup restored successfully!")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Info: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Error during restore: {e}", file=sys.stderr)
        if e.stdout:
            print(f"Output: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"Error details: {e.stderr}", file=sys.stderr)
        # Try to start container anyway
        try:
            subprocess.run(["docker", "start", CONTAINER_NAME], capture_output=True)
            print("Container restarted.")
        except:
            pass
        return False
    
    # Start the original container
    print("Starting Neo4j container...")
    try:
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True, capture_output=True)
        print("Container started.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not start container: {e}", file=sys.stderr)
        return False
    
    # Wait for Neo4j to be ready, then start the database
    print("Waiting for Neo4j service to be ready...")
    max_wait = 30
    wait_interval = 2
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            driver = GraphDatabase.driver(
                "bolt://localhost:7687",  # Use system database connection
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=5
            )
            driver.verify_connectivity()
            driver.close()
            break
        except Exception:
            time.sleep(wait_interval)
            elapsed += wait_interval
            if elapsed % 4 == 0:
                print(f"Waiting for Neo4j... ({elapsed}s)")
    
    # Start the neo4j database explicitly
    print("Starting the 'neo4j' database...")
    try:
        start_db_cmd = [
            "docker", "exec", CONTAINER_NAME,
            "cypher-shell", "-u", NEO4J_USER, "-p", NEO4J_PASSWORD,
            "-d", "system",
            "START DATABASE neo4j;"
        ]
        result = subprocess.run(start_db_cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("Database 'neo4j' started successfully.")
        else:
            print(f"Note: Database start command returned: {result.stderr or result.stdout}")
    except Exception as e:
        print(f"Note: Could not start database via cypher-shell: {e}")
        print("Database may start automatically. Please check manually if needed.")
    
    return True


def copy_backup_to_container(backup_path):
    """Copy backup file into the Docker container."""
    print(f"Copying backup file to container...")
    try:
        # Use absolute path for the backup file
        backup_path_abs = backup_path.resolve()
        container_backup_dir = "/tmp"
        container_backup_path = f"{container_backup_dir}/{Path(backup_path).name}"
        
        # Copy file directly into container (docker cp source destination)
        # Format: docker cp /host/path/file container:/container/path/
        result = subprocess.run(
            ["docker", "cp", str(backup_path_abs), f"{CONTAINER_NAME}:{container_backup_dir}/"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"Backup file copied to container at {container_backup_path}")
        return container_backup_path
    except subprocess.CalledProcessError as e:
        print(f"Error copying backup file to container: {e}", file=sys.stderr)
        if e.stderr:
            print(f"Error details: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error copying backup file to container: {e}", file=sys.stderr)
        return None


def restore_backup(container_backup_path):
    """Restore Neo4j backup using neo4j-admin."""
    print(f"Restoring backup from {container_backup_path}...")
    backup_filename = Path(container_backup_path).name
    
    # Try Neo4j 5.x format first (neo4j-admin database restore)
    backup_file_path = f"/tmp/{backup_filename}"
    restore_commands = [
        # Format 1: --from-path points directly to backup file, --overwrite-destination, database name as positional arg
        [
            "docker", "exec", "-e", "NEO4J_ACCEPT_LICENSE_AGREEMENT=yes", CONTAINER_NAME,
            "neo4j-admin", "database", "restore",
            f"--from-path={backup_file_path}",
            "--overwrite-destination=true",
            "neo4j"
        ],
        # Format 2: --from-path points to directory, backup file only (database name detected from backup)
        [
            "docker", "exec", "-e", "NEO4J_ACCEPT_LICENSE_AGREEMENT=yes", CONTAINER_NAME,
            "neo4j-admin", "database", "restore",
            "--from-path=/tmp",
            "--overwrite-destination=true",
            backup_filename
        ],
    ]
    
    for i, restore_command in enumerate(restore_commands, 1):
        try:
            print(f"Trying restore command format {i}...")
            result = subprocess.run(
                restore_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("Backup restored successfully!")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Info: {result.stderr}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Command format {i} failed: {e.stderr if e.stderr else e.stdout}")
            if i < len(restore_commands):
                continue
            else:
                print(f"\nAll restore command formats failed.", file=sys.stderr)
                print(f"Last error output: {e.stdout}", file=sys.stderr)
                print(f"Last error details: {e.stderr}", file=sys.stderr)
                return False
    
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_neo4j_backup.py <backup_file_path>", file=sys.stderr)
        print(f"Example: python import_neo4j_backup.py backup/final-neo4j-2026-02-18T05-11-05-4dbac81f.backup", file=sys.stderr)
        sys.exit(1)
    
    backup_path = Path(sys.argv[1])
    
    if not backup_path.exists():
        print(f"Error: Backup file not found: {backup_path}", file=sys.stderr)
        sys.exit(1)
    
    # Check if running in Docker
    if not check_docker_container():
        print(f"Error: Neo4j Docker container '{CONTAINER_NAME}' is not running.", file=sys.stderr)
        print("Please start the container first with: docker start graph-rag-neo4j", file=sys.stderr)
        sys.exit(1)
    
    print(f"Importing Neo4j backup: {backup_path}")
    print("=" * 60)
    
    # Step 1: Reset current database
    print("\nStep 1: Resetting current database...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        deleted = clear_graph(driver)
        print(f"Deleted {deleted} nodes and all relationships.")
        driver.close()
    except Exception as e:
        print(f"Error resetting database: {e}", file=sys.stderr)
        print("Continuing with backup restore anyway...", file=sys.stderr)
    
    # Step 2: Try to set database offline and restore while container is running
    database_offline = set_database_offline()
    
    if database_offline:
        # Copy backup to container
        container_backup_path = copy_backup_to_container(backup_path)
        if not container_backup_path:
            print("Failed to copy backup file to container. Aborting.", file=sys.stderr)
            set_database_online()  # Try to bring database back online
            sys.exit(1)
        
        # Restore backup (database is offline, container is running)
        if not restore_backup(container_backup_path):
            print("Failed to restore backup. Aborting.", file=sys.stderr)
            set_database_online()  # Try to bring database back online
            sys.exit(1)
        
        # Set database online
        if not set_database_online():
            print("Warning: Could not set database online. Please check manually.", file=sys.stderr)
    else:
        # Fallback: Stop container and use volumes approach
        print("\nUsing alternative restore method (stopping container)...")
        if not restore_with_stopped_container(backup_path):
            print("Failed to restore backup using alternative method. Aborting.", file=sys.stderr)
            sys.exit(1)
        
        # Wait for container to be ready
        print("Waiting for Neo4j to be ready...")
        max_wait = 60
        wait_interval = 2
        elapsed = 0
        
        while elapsed < max_wait:
            try:
                driver = GraphDatabase.driver(
                    NEO4J_URI,
                    auth=(NEO4J_USER, NEO4J_PASSWORD),
                    connection_timeout=5
                )
                driver.verify_connectivity()
                driver.close()
                print("Neo4j is ready!")
                break
            except Exception:
                time.sleep(wait_interval)
                elapsed += wait_interval
                print(f"Waiting for Neo4j... ({elapsed}s)")
    
    print("\n" + "=" * 60)
    print("Backup import completed successfully!")
    print(f"Database restored from: {backup_path}")


if __name__ == "__main__":
    sys.exit(main())
