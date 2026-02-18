# MCP Setup and Usage Guide

This guide explains how to set up and run the Asset Graph RAG MCP server, configure MCP tools, and use them in Cursor.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Setup](#project-setup)
3. [Neo4j Configuration](#neo4j-configuration)
4. [MCP Server Configuration](#mcp-server-configuration)
5. [Running the MCP Server](#running-the-mcp-server)
6. [Using MCP Tools in Cursor](#using-mcp-tools-in-cursor)
7. [Available MCP Tools](#available-mcp-tools)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before setting up the MCP server, ensure you have:

- **Python 3.8+** installed
- **Neo4j Database** running (version 5.x recommended)
- **Cursor IDE** installed
- **Virtual environment** (recommended)

---

## Project Setup

### 1. Clone or Navigate to the Project

```bash
cd /path/to/graph-sensa-rnd
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python3 -m venv env

# Activate virtual environment
# On macOS/Linux:
source env/bin/activate
# On Windows:
# env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The project requires:
- `neo4j>=5.14.0` - Neo4j Python driver
- `fastmcp>=2.0,<3` - FastMCP framework for MCP servers
- `python-dotenv>=1.0.0` - Environment variable management

---

## Neo4j Configuration

### 1. Set Up Neo4j Database

Ensure your Neo4j database is running. You can use:
- **Neo4j Desktop** (recommended for local development)
- **Neo4j Community Edition** (standalone)
- **Neo4j Aura** (cloud-hosted)

### 2. Configure Environment Variables

Create a `.env` file in the project root (or update the existing one):

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_CONNECTION_TIMEOUT=15
```

**Important:** Replace `your_password_here` with your actual Neo4j password.

### 3. Verify Neo4j Connection

You can test the connection by running:

```bash
python -c "from neo4j_config import get_driver; driver = get_driver(); print('Connected!' if driver else 'Failed'); driver.close()"
```

---

## MCP Server Configuration

### MCP Configuration File Location

The MCP configuration file for Cursor is located at:
```
~/.cursor/mcp.json
```

On macOS/Linux, this expands to:
```
/Users/your_username/.cursor/mcp.json
```

On Windows:
```
C:\Users\your_username\AppData\Roaming\Cursor\User\globalStorage\mcp.json
```

### Example mcp.json Configuration

Here's a complete example `mcp.json` file:

```json
{
    "mcpServers": {
        "asset-graph-rag": {
            "command": "/absolute/path/to/graph-sensa-rnd/env/bin/python",
            "args": [
                "/absolute/path/to/graph-sensa-rnd/main.py"
            ],
            "cwd": "/absolute/path/to/graph-sensa-rnd",
            "env": {
                "NEO4J_URI": "bolt://localhost:7687",
                "NEO4J_USERNAME": "neo4j",
                "NEO4J_PASSWORD": "your_password_here"
            }
        }
    }
}
```

### Configuration Options Explained

- **`mcpServers`**: Object containing all MCP server configurations
- **`asset-graph-rag`**: Server identifier (can be any name you prefer)
- **`command`**: Full path to the Python interpreter in your virtual environment
- **`args`**: Array of arguments passed to the Python interpreter (the main.py file)
- **`cwd`**: Working directory for the MCP server process
- **`env`** (optional): Environment variables to pass to the server process

### Important Notes

1. **Use Absolute Paths**: Always use absolute paths in `mcp.json`, not relative paths
2. **Virtual Environment**: Point `command` to the Python executable in your virtual environment (`env/bin/python`)
3. **Environment Variables**: You can either:
   - Set them in `mcp.json` under `env` (as shown above)
   - Or rely on the `.env` file in the project directory (recommended)
4. **Multiple Servers**: You can add multiple MCP servers to the `mcpServers` object

### Example with Multiple Servers

```json
{
    "mcpServers": {
        "asset-graph-rag": {
            "command": "/Users/cefalo/Documents/graph-sensa-rnd/env/bin/python",
            "args": [
                "/Users/cefalo/Documents/graph-sensa-rnd/main.py"
            ],
            "cwd": "/Users/cefalo/Documents/graph-sensa-rnd"
        },
        "another-mcp-server": {
            "command": "/path/to/another/server/venv/bin/python",
            "args": [
                "/path/to/another/server/main.py"
            ],
            "cwd": "/path/to/another/server"
        }
    }
}
```

---

## Running the MCP Server

### Method 1: Direct Execution (Testing)

You can run the MCP server directly for testing:

```bash
# Activate virtual environment
source env/bin/activate

# Run the server
python main.py
```

The server will start and wait for MCP protocol messages via stdin/stdout.

### Method 2: Through Cursor (Production)

Once configured in `mcp.json`, Cursor will automatically start the MCP server when needed. The server runs in the background and communicates with Cursor through the MCP protocol.

### Method 3: Standalone Testing

For debugging, you can test individual tools:

```bash
python -c "from tools.get_node_by_name import get_node_by_name; print(get_node_by_name('Biofilter 11'))"
```

---

## Using MCP Tools in Cursor

### 1. Verify MCP Server is Running

After configuring `mcp.json`:
1. Restart Cursor IDE
2. Open the MCP panel (usually accessible via Command Palette: `Cmd+Shift+P` → "MCP")
3. Check that `asset-graph-rag` appears in the list of available servers

### 2. Using Tools in Chat

Once the MCP server is connected, you can use natural language queries:

**Example Queries:**
- "How many assets are in Biofilter 11?"
- "List all categories in the graph"
- "What is connected to Hall 4?"
- "Count assets by category"
- "How many locations are there?"

The AI assistant will automatically use the appropriate MCP tools to answer your questions.

### 3. Direct Tool Invocation

You can also directly invoke tools in your prompts:

```
Use the get_node_by_name tool to find "Biofilter 11"
```

---

## Available MCP Tools

The Asset Graph RAG MCP server provides the following tools:

### Node Discovery Tools

- **`get_node_by_name(name)`**: Find a single node by name across all node types (Location, System, Asset, Category)
- **`count_nodes_by_name(name)`**: Count nodes with an exact name match
- **`count_by_label(label)`**: Count all nodes with a specific label (e.g., "Asset", "Location")

### Category Tools

- **`list_categories(include_hierarchy=True)`**: List all Category nodes and their BELONGS_TO hierarchy
- **`count_assets_by_category(category_scope='both')`**: Count assets per location and system categories

### Connection Tools

- **`describe_node_connections(name, include_attributes=False)`**: Show all incoming and outgoing relationships for a node

### Container Content Tools

- **`container_contents_count_by_name(name, relationship_types, target_label=None, name_match='exact', parent_location_name=None, validity_filter=None)`**: Count items in a container by name
  - Use `name_match='prefix'` for partial matches (e.g., "Hall" matches "Hall 1", "Hall 2")
  
- **`container_contents_list_by_name(name, relationship_types, target_label=None, name_match='exact', parent_location_name=None, validity_filter=None, limit=1000)`**: List items in a container by name

- **`container_contents_count(start_node_id, relationship_types, target_label=None, validity_filter=None)`**: Count items in a container using node_id

- **`container_contents_list(start_node_id, relationship_types, target_label=None, validity_filter=None, limit=1000, include_attributes=None)`**: List items in a container using node_id

### Summary Tools

- **`count_assets_breakdown(container_type='Both', validity_filter=None)`**: Full breakdown of assets per Location and/or System

### Common Use Cases

**Count assets in a location:**
```python
container_contents_count_by_name(
    name="Biofilter 11",
    relationship_types=["LOCATED_IN"],
    target_label="Asset"
)
```

**List all halls:**
```python
container_contents_list_by_name(
    name="Hall",
    relationship_types=["LOCATED_IN"],
    target_label="Location",
    name_match="prefix"
)
```

**Get category hierarchy:**
```python
list_categories(include_hierarchy=True)
```

---

## Troubleshooting

### MCP Server Not Starting

1. **Check Python Path**: Verify the `command` path in `mcp.json` points to a valid Python executable
2. **Check File Paths**: Ensure all paths in `mcp.json` are absolute and correct
3. **Check Permissions**: Ensure the Python executable and main.py are executable
4. **Check Logs**: Look for error messages in Cursor's MCP panel or console

### Connection Errors

1. **Neo4j Not Running**: Ensure Neo4j is running and accessible
2. **Wrong Credentials**: Verify `.env` file has correct Neo4J credentials
3. **Network Issues**: Check if `NEO4J_URI` is correct (default: `bolt://localhost:7687`)

### Import Errors

1. **Dependencies Missing**: Run `pip install -r requirements.txt`
2. **Virtual Environment**: Ensure you're using the correct virtual environment
3. **Python Version**: Verify Python 3.8+ is installed

### Tools Not Available in Cursor

1. **Restart Cursor**: After modifying `mcp.json`, restart Cursor completely
2. **Check MCP Panel**: Verify the server appears in the MCP panel
3. **Check Server Logs**: Look for errors in the MCP server logs

### Common Error Messages

**"Connection refused"**
- Neo4j is not running or URI is incorrect

**"Authentication failed"**
- Check `NEO4J_USERNAME` and `NEO4J_PASSWORD` in `.env`

**"Module not found"**
- Install dependencies: `pip install -r requirements.txt`

**"Command not found"**
- Verify the Python path in `mcp.json` is correct

---

## Example Workflow

1. **Set up environment:**
   ```bash
   cd /path/to/graph-sensa-rnd
   python3 -m venv env
   source env/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Neo4j:**
   ```bash
   # Edit .env file
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password
   ```

3. **Configure MCP:**
   ```bash
   # Edit ~/.cursor/mcp.json
   # Add the asset-graph-rag server configuration
   ```

4. **Restart Cursor:**
   - Close Cursor completely
   - Reopen Cursor
   - Verify MCP server is connected

5. **Test the setup:**
   - Ask: "How many assets are in the graph?"
   - Or: "List all categories"

---

## Additional Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Neo4j Python Driver Documentation](https://neo4j.com/docs/python-manual/current/)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the MCP server logs in Cursor
3. Verify your Neo4j database is properly configured
4. Ensure all dependencies are installed correctly
