# Neo4j Asset Graph RAG with FastMCP

This folder contains a **Neo4j-based RAG (Retrieval-Augmented) application** that exposes the Asset Graph via **FastMCP** so an LLM can answer natural language questions (e.g. *"Count the number of items in Biofilter 11"*) using generic tools instead of writing Cypher.

## Contents

| File                    | Purpose                                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------------------- |
| `neo4j_dummy_data.json` | Dummy nodes and relationships to load into Neo4j (Categories, Locations, Systems, Assets, Signals). |
| `load_neo4j.py`         | Script to clear the DB and load `neo4j_dummy_data.json` into Neo4j.                                 |
| `neo4j_rag_mcp.py`      | FastMCP server exposing `get_node_by_name` and `aggregate_incoming`.                            |
| `requirements.txt`      | Python dependencies (neo4j, fastmcp, python-dotenv).                                                |
| `.env`                  | Optional; set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD (defaults in code if unset).                    |

## 1. Dummy data: `neo4j_dummy_data.json`

Use this file to feed dummy nodes and relationships into Neo4j.

- **Structure:**  
  - `nodes`: array of `{ unique_id, labels[], name, fingerprint, description, ... }`.  
  - `relationships`: array of `{ from_unique_id, to_unique_id, type, validity_from, validity_to }`.

- **Layers:**  
  - **Layer 0:** Categories (SITE, PLANT, SECTION, SUB-SECTION) with `BELONGS_TO`.  
  - **Layer 1:** Locations (Aardal, Hall 1, Hall 4, Tank Area, Tank 1, Biofilter 11, Reservoir100, CenterChannel), Systems (FeedStorage, Feeding System, Oxygen System, Filtration System), MeasuringUnit (km/h).  
  - **Layer 2:** Assets (e.g. TSL_FIT001, TGL_10P001_00, Oxygen Sensor, Pump_001, Valve_V001) with `LOCATED_IN` and `PART_OF_SYSTEM`.  
  - **Layer 3:** Signals (Flow_RAW, Flow_1_min_AVG_CLEAN, etc.) with `MEASURES` to assets.

You can edit this JSON to add more nodes/entities and re-run the loader.

## 2. Setup

```bash
# Create venv and install
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Configure Neo4j: create a .env file with:
#   NEO4J_URI=neo4j://localhost:7687
#   NEO4J_USER=neo4j
#   NEO4J_PASSWORD=password
```

## 3. Load dummy data into Neo4j

Ensure Neo4j is running, then:

```bash
python load_neo4j.py
```

This will:

- Clear the graph.
- Create all nodes from `neo4j_dummy_data.json`.
- Create all relationships with `validity_from` / `validity_to`.
- Create indexes on `unique_id` for each label.

## 4. Run the MCP server

```bash
python neo4j_rag_mcp.py
```

Or with FastMCP CLI (if you use it):

```bash
fastmcp run neo4j_rag_mcp.py
```

---

## 5. How to use the MCP tools

### Option A: Use in Cursor (or another MCP client)

1. **Add the server to Cursor’s MCP config**  
   - Open **Cursor Settings → MCP** and add a new server, or edit the config file (e.g. `~/.cursor/mcp.json` or via **Cursor Settings → MCP → Edit config**).  
   - Add a server that runs your FastMCP app. Example (replace the path with your project path):

   ```json
   {
     "mcpServers": {
       "asset-graph-rag": {
         "command": "python",
         "args": ["/Users/sohan/Documents/graph-sensa-rnd/neo4j_rag_mcp.py"],
         "cwd": "/Users/sohan/Documents/graph-sensa-rnd",
         "env": {}
       }
     }
   }
   ```

   Use a **Python that exists** (either system Python or your venv). If you get `ENOENT` when starting the server, the `command` path is wrong—e.g. no `.venv` in the project. Use one of these:

   ```json
   "command": "python3",
   "args": ["/Users/sohan/Documents/graph-sensa-rnd/neo4j_rag_mcp.py"],
   "cwd": "/Users/sohan/Documents/graph-sensa-rnd"
   ```

   Or, if you have a venv and want to use it, set `command` to the **full path** to that venv’s `python` (e.g. `"/path/to/your/.venv/bin/python"`). Run `which python3` in the project to see the path.

2. **Start Cursor (or restart)** so it starts the MCP server. The tools `get_node_by_name` and `aggregate_incoming` will show up for the AI.

3. **Ask in natural language** in the Cursor chat, for example:
   - *“Count the number of items in Biofilter 11”*
   - *“List all assets in the Feeding System”*
   - *“How many items are in Hall 4?”*

   The AI will call the MCP tools (lookup location/system, then traverse and aggregate) and answer from the graph.

### Option B: Call the tools from a script (no LLM)

Run the test script that calls the tools directly (Neo4j and data must be loaded first):

```bash
python test_mcp_tools.py
```

See `test_mcp_tools.py` for the exact arguments. You can copy that pattern to call the tools from your own code.

---

The LLM (or your script) can call:

1. **`get_node_by_name`** – Find a node by `label` and `name`; returns `node_id` (Neo4j `element_id`) and attributes.  
2. **`aggregate_incoming`** – From a `start_node_id`, run a single Cypher query: match nodes that have INCOMING relationships of the given types to the start node, filter by `target_label` (e.g. Asset), and `aggregation` (`count` or `list`, or sum/avg/min/max with `property_name`). Supports `validity_filter` (e.g. `current_only`).

Example flow for *"Count the number of items in Biofilter 11"*:

1. `get_node_by_name(label="Location", name="Biofilter 11")` → get `node_id`.
2. `aggregate_incoming(start_node_id=..., relationship_types=["LOCATED_IN"], target_label="Asset", aggregation="count", validity_filter={"current_only": true})` → get count.

## 6. Example questions the graph can answer (with dummy data)

- Count items in **Biofilter 11** (3 assets: Oxygen Sensor, Pump_001, Valve_V001).  
- Count items in **Hall 4** (1 asset: Hall4_ControlPanel).  
- Count items in **Reservoir100** (1 asset: TSL_FIT002).  
- Count items in **CenterChannel** (1 asset: TGL_10P002_00).  
- List assets in **Feeding System**.  
- List assets in **Tank 1**.

All of these use the same two generic tools; no custom Cypher is required from the LLM.
