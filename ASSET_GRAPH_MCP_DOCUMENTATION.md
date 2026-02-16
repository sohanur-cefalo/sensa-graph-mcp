# Asset Graph Model + MCP R&D Documentation

## Table of Contents

1. [Overview](#overview)
2. [Goals](#goals)
3. [Graph Model Structure](#graph-model-structure)
4. [Layer Details](#layer-details)
5. [Relationship Validity](#relationship-validity)
6. [Query Patterns](#query-patterns)
7. [Problem Statement](#problem-statement)
8. [MCP Solution Design](#mcp-solution-design)
9. [Architecture](#architecture)
10. [Design Principles](#design-principles)
11. [Implementation Examples](#implementation-examples)
12. [Future Extensions](#future-extensions)

---

## Overview

This document describes a layered asset knowledge graph built on Neo4j and a Model Context Protocol (MCP) solution for enabling natural language queries over the graph structure. The system is designed to answer questions about physical assets, their locations, systems, and associated time-series data through a generic, composable tool interface.

---

## Goals

The primary goal is to enable natural language question answering over a layered asset knowledge graph. Example questions include:

- **Count the number of items in Biofilter 11**
- **Count the number of items in Hall 4**
- **Count the number of items in Reservoir100**
- **Count the number of items in CenterChannel**

These questions should be answered through generic MCP tools that abstract away the complexity of Cypher query generation, allowing the LLM to focus on reasoning rather than database-specific logic.

---

## Graph Model Structure

The graph model is organized into **four hierarchical layers**, each representing a different level of abstraction:

```
Layer 0 → Category (Taxonomy/Classification)
Layer 1 → Context (Location / System / Measuring Unit)
Layer 2 → Asset (Physical Equipment)
Layer 3 → Signal (Time-series Data)
```

### Layer Hierarchy Visualization

```
Category (Layer 0)
    ↓
Context (Layer 1) - Location / System / Measuring Unit
    ↓
Asset (Layer 2) - Physical Equipment
    ↓
Signal (Layer 3) - Time-series Data
```

---

## Layer Details

### Layer 0 — Category

**Purpose:** Represents classification hierarchy and structural taxonomy.

**Node Label:** `Category`

**Attributes:**
- `name` (String): Category name
- `unique_id` (String): Unique identifier
- `fingerprint` (String): Hash/fingerprint for versioning
- `description` (String): Human-readable description
- `embedding` (Vector): Semantic embedding vector

**Examples:**
- `SITE`
- `PLANT`
- `SECTION`
- `SUB-SECTION`

**Relationships:**
- `(:Category)-[:BELONGS_TO]->(:Category)`
  - Creates hierarchical category structure
  - Example: `SUB-SECTION` → `BELONGS_TO` → `SECTION` → `BELONGS_TO` → `PLANT`

**Key Characteristics:**
- Defines structural taxonomy, not physical objects
- Enables classification of contexts and assets
- Supports hierarchical organization

---

### Layer 1 — Context

**Purpose:** Represents real-world structural dimensions (locations, systems, measuring units).

**Node Labels:** `Location`, `System`, `MeasuringUnit`

**Attributes:**
- `name` (String): Context name
- `unique_id` (String): Unique identifier
- `fingerprint` (String): Hash/fingerprint for versioning
- `description` (String): Human-readable description
- `embedding` (Vector): Semantic embedding vector

#### Location Dimension

**Examples:**
- `Aardal` (Site level)
- `Hall 1` (Building/Hall level)
- `Tank Area` (Area level)
- `Tank 1` (Specific tank)
- `Biofilter 11` (Specific equipment location)
- `Hall 4`
- `Reservoir100`
- `CenterChannel`

**Relationships:**
- `(:Location)-[:LOCATED_IN]->(:Location)`
  - Creates hierarchical location structure
  - Example: `Tank 1` → `LOCATED_IN` → `Tank Area` → `LOCATED_IN` → `Hall 1` → `LOCATED_IN` → `Aardal`
- `(:Location)-[:BELONGS_TO_LOCATION_CATEGORY]->(:Category)`
  - Links location to its category classification
  - Example: `Hall 1` → `BELONGS_TO_LOCATION_CATEGORY` → `PLANT`

**Location Hierarchy Example:**
```
Aardal (Site)
  └─ Hall 1
      └─ Tank Area
          └─ Tank 1
              └─ Biofilter 11
```

#### System Dimension

**Examples:**
- `Feeding System`
- `FeedStorage`
- `Oxygen System`
- `Filtration System`

**Relationships:**
- `(:System)-[:PART_OF_SYSTEM]->(:System)`
  - Creates hierarchical system structure
  - Example: `Feeding System` → `PART_OF_SYSTEM` → `FeedStorage`
- `(:System)-[:BELONGS_TO_SYSTEM_CATEGORY]->(:Category)`
  - Links system to its category classification
  - Example: `Feeding System` → `BELONGS_TO_SYSTEM_CATEGORY` → `SYSTEM`

**System Hierarchy Example:**
```
FeedStorage
  └─ Feeding System
```

#### Measuring Unit Dimension

**Purpose:** Represents units of measurement for signals and assets.

**Relationships:**
- Similar pattern to Location and System
- Links to Category via `BELONGS_TO_MEASURING_UNIT_CATEGORY`

---

### Layer 2 — Asset

**Purpose:** Represents physical equipment and devices.

**Node Label:** `Asset`

**Attributes:**
- `name` (String): Asset name/identifier
- `unique_id` (String): Unique identifier
- `fingerprint` (String): Hash/fingerprint for versioning
- `description` (String): Human-readable description
- `embedding` (Vector): Semantic embedding vector

**Examples:**
- `TSL_FIT001` (Flow sensor)
- `TGL_10P001_00` (Tank level sensor)
- `Oxygen Sensor`
- `Pump_001`
- `Valve_V001`

**Relationships:**
- `(:Asset)-[:LOCATED_IN]->(:Location)`
  - Links asset to its physical location
  - Example: `TSL_FIT001` → `LOCATED_IN` → `Tank 1`
- `(:Asset)-[:PART_OF_SYSTEM]->(:System)`
  - Links asset to its functional system
  - Example: `TSL_FIT001` → `PART_OF_SYSTEM` → `Feeding System`

**Key Characteristics:**
- An asset can belong to **both** a location and a system simultaneously
- Assets are the primary entities that users query about ("items", "equipment", "devices")
- Assets bridge the physical (location) and functional (system) dimensions

**Example Asset Relationships:**
```
TGL_10P001_00
  ├─ LOCATED_IN → Tank 1
  └─ PART_OF_SYSTEM → Feeding System
```

---

### Layer 3 — Signal

**Purpose:** Represents time-series data streams associated with assets.

**Node Label:** `Signal`

**Attributes:**
- `name` (String): Signal name
- `unique_id` (String): Unique identifier (linked to Influx GUID)
- `fingerprint` (String): Hash/fingerprint for versioning
- `description` (String): Human-readable description
- `embedding` (Vector): Semantic embedding vector
- `influx_guid` (String): InfluxDB identifier
- `metadata` (JSON): Additional metadata for Influx access

**Examples:**
- `Flow_RAW` (Raw flow measurement)
- `Flow_1_min_AVG_CLEAN` (1-minute averaged, cleaned)
- `Flow_1_hour_AVG_CLEAN` (1-hour averaged, cleaned)
- `Temperature_RAW`
- `Pressure_AVG`

**Relationships:**
- `(:Signal)-[:MEASURES]->(:Asset)`
  - Links signal to the asset it measures
  - Example: `Flow_RAW` → `MEASURES` → `TSL_FIT001`

**Versioning:**
- When signal version changes:
  - New signal node is created
  - Edge validity is updated
  - Historical structure is preserved

**Key Characteristics:**
- Signals contain metadata for accessing time-series data in InfluxDB
- Multiple signals can measure the same asset (different aggregations, cleaning levels)
- Signals enable time-series analysis and monitoring

---

## Relationship Validity

All edges in the graph contain temporal validity attributes:

- `validity_from` (DateTime): When the relationship becomes valid
- `validity_to` (DateTime): When the relationship expires (null for current)

**Purpose:**
- Enables temporal queries
- Supports historical structure reconstruction
- Handles versioning and changes over time
- Allows "as-of-date" queries

**Example Edge Properties:**
```cypher
{
  validity_from: "2024-01-01T00:00:00Z",
  validity_to: null  // Current relationship
}
```

**Temporal Query Example:**
```cypher
// Find assets in Tank 1 as of 2023-06-01
MATCH (l:Location {name: "Tank 1"})
MATCH (a:Asset)-[r:LOCATED_IN]->(l)
WHERE r.validity_from <= datetime("2023-06-01T00:00:00Z")
  AND (r.validity_to IS NULL OR r.validity_to >= datetime("2023-06-01T00:00:00Z"))
RETURN a
```

---

## Query Patterns

### Example Question: "Count the number of items in Biofilter 11"

**Interpretation:**
- `Biofilter 11` → Location node
- `items` → Assets
- Count Assets that have `LOCATED_IN` → `Biofilter 11`

**Conceptual Cypher:**
```cypher
MATCH (l:Location {name: "Biofilter 11"})
MATCH (a:Asset)-[:LOCATED_IN]->(l)
WHERE r.validity_to IS NULL  // Only current relationships
RETURN count(a) AS asset_count
```

**Graph Solution Process:**
1. **Node Lookup:** Find Location node by name "Biofilter 11"
2. **Relationship Traversal:** Follow `LOCATED_IN` edges (incoming to location)
3. **Filtering:** Apply validity constraints (current relationships only)
4. **Aggregation:** Count matching Asset nodes

### Example Question: "Count the number of items in Hall 4"

**Conceptual Cypher:**
```cypher
MATCH (l:Location {name: "Hall 4"})
MATCH (a:Asset)-[:LOCATED_IN]->(l)
WHERE r.validity_to IS NULL
RETURN count(a) AS asset_count
```

### Example Question: "List all assets in Feeding System"

**Conceptual Cypher:**
```cypher
MATCH (s:System {name: "Feeding System"})
MATCH (a:Asset)-[:PART_OF_SYSTEM]->(s)
WHERE r.validity_to IS NULL
RETURN a.name, a.unique_id, a.description
```

### Example Question: "Find all signals measuring assets in Tank 1"

**Conceptual Cypher:**
```cypher
MATCH (l:Location {name: "Tank 1"})
MATCH (a:Asset)-[:LOCATED_IN]->(l)
MATCH (sig:Signal)-[:MEASURES]->(a)
WHERE r.validity_to IS NULL
RETURN sig.name, sig.unique_id, a.name
```

---

## Problem Statement

### Current Challenges

1. **LLM Should Not Generate Raw Cypher**
   - Cypher is database-specific and error-prone
   - LLMs may generate invalid or unsafe queries
   - Hard to validate and secure

2. **Hardcoded Tools Don't Scale**
   - Creating tools like `count_assets_in_hall`, `count_assets_in_tank` for each use case is not maintainable
   - New questions require new tools
   - Code duplication and maintenance burden

3. **Graph Complexity**
   - Multiple relationship types (`LOCATED_IN`, `PART_OF_SYSTEM`, `BELONGS_TO`, etc.)
   - Validity constraints on all edges
   - Multiple node labels and hierarchies
   - Complex traversal patterns

4. **Need for Generic, Reusable Patterns**
   - Same traversal logic applies across different contexts
   - Aggregation patterns are universal
   - Node lookup is a common operation

---

## MCP Solution Design

The solution exposes **generic, composable tools** instead of use-case-specific tools.

### Tool 1: `get_node_by_name`

**Purpose:** Find a node by label and name attribute.

**Parameters:**
- `label` (String, required): Node label (e.g., "Location", "System", "Asset", "Category")
- `name` (String, required): Name attribute value to search for
- `include_attributes` (Array[String], optional): Specific attributes to return (default: all)

**Returns:**
- `node_id` (String): Unique node identifier
- `label` (String): Node label
- `attributes` (Object): Node attributes
- `found` (Boolean): Whether node was found

**Example Usage:**
```json
{
  "label": "Location",
  "name": "Biofilter 11"
}
```

**Internal Cypher (MCP handles this):**
```cypher
MATCH (n:Location {name: "Biofilter 11"})
RETURN n
LIMIT 1
```

**Response:**
```json
{
  "found": true,
  "node_id": "123",
  "label": "Location",
  "attributes": {
    "name": "Biofilter 11",
    "unique_id": "LOC_BIOFILTER_11",
    "description": "Biofilter unit 11",
    "fingerprint": "abc123..."
  }
}
```

---

### Tool 2: `aggregate_incoming`

**Purpose:** Traverse relationships from a starting node and aggregate results.

**Parameters:**
- `start_node_id` (String, required): Starting node identifier
- `relationship_types` (Array[String], required): Relationship types to traverse (e.g., ["LOCATED_IN", "PART_OF_SYSTEM"])
- `direction` (String, required): Traversal direction - `INCOMING`, `OUTGOING`, or `BOTH`
- `target_label` (String, optional): Filter results by target node label (e.g., "Asset", "Location")
- `aggregation` (String, required): Aggregation operation - `count`, `list`, `sum`, `avg`, `min`, `max`
- `validity_filter` (Object, optional): Temporal filtering
  - `as_of_date` (DateTime, optional): Query as of specific date
  - `current_only` (Boolean, optional): Only current relationships (default: true)
- `limit` (Integer, optional): Maximum results for list aggregation (default: 1000)
- `include_attributes` (Array[String], optional): Attributes to include in list results

**Returns:**
- `result` (Number | Array): Aggregation result (count, list of nodes, etc.)
- `relationship_count` (Integer): Number of relationships traversed
- `target_nodes_found` (Integer): Number of target nodes matched

**Example Usage:**
```json
{
  "start_node_id": "123",
  "relationship_types": ["LOCATED_IN"],
  "direction": "INCOMING",
  "target_label": "Asset",
  "aggregation": "count",
  "validity_filter": {
    "current_only": true
  }
}
```

**Internal Cypher (MCP handles this):**
```cypher
MATCH (start)
WHERE id(start) = 123
MATCH (target:Asset)-[r:LOCATED_IN]->(start)
WHERE r.validity_to IS NULL
RETURN count(target) AS result
```

**Response:**
```json
{
  "result": 15,
  "relationship_count": 15,
  "target_nodes_found": 15
}
```

**List Aggregation Example:**
```json
{
  "start_node_id": "123",
  "relationship_types": ["LOCATED_IN"],
  "direction": "INCOMING",
  "target_label": "Asset",
  "aggregation": "list",
  "include_attributes": ["name", "unique_id", "description"],
  "limit": 100
}
```

**Response:**
```json
{
  "result": [
    {
      "node_id": "456",
      "name": "TSL_FIT001",
      "unique_id": "ASSET_TSL_FIT001",
      "description": "Flow sensor"
    },
    {
      "node_id": "457",
      "name": "TGL_10P001_00",
      "unique_id": "ASSET_TGL_10P001_00",
      "description": "Tank level sensor"
    }
  ],
  "relationship_count": 15,
  "target_nodes_found": 15
}
```

---

### Tool 3: `find_nodes_by_semantic_similarity` (Future Extension)

**Purpose:** Find nodes using semantic embeddings.

**Parameters:**
- `query_text` (String, required): Natural language query
- `label` (String, optional): Filter by node label
- `top_k` (Integer, optional): Number of results (default: 10)
- `similarity_threshold` (Float, optional): Minimum similarity score

**Returns:**
- `nodes` (Array): List of similar nodes with similarity scores

---

## Architecture

### System Flow

```
┌─────────┐
│   LLM   │  (Natural Language Understanding)
└────┬────┘
     │
     │ "Count items in Biofilter 11"
     │
     ▼
┌─────────────────┐
│ Supervisor Agent│  (Orchestrates tool calls)
└────────┬────────┘
         │
         │ 1. get_node_by_name("Location", "Biofilter 11")
         │ 2. aggregate_incoming(node_id, "LOCATED_IN", "INCOMING", "Asset", "count")
         │
         ▼
┌─────────────────┐
│   MCP Tools     │  (Generic graph access)
└────────┬────────┘
         │
         │ Generates safe Cypher queries
         │ Validates parameters
         │ Applies security constraints
         │
         ▼
┌─────────────────┐
│     Neo4j       │  (Graph database)
└─────────────────┘
```

### Component Responsibilities

**LLM:**
- **WHAT** is needed (intent understanding)
- Natural language interpretation
- Tool selection and parameterization
- Result interpretation

**Supervisor Agent:**
- Tool orchestration
- Multi-step query planning
- Error handling and retries

**MCP Tools:**
- **HOW** to query (Cypher generation)
- Parameter validation
- Security and access control
- Query optimization
- Result formatting

**Neo4j:**
- Graph storage
- Query execution
- Relationship traversal
- Index management

---

## Design Principles

### ✅ DO: Create Generic, Composable Tools

**Generic Traversal:**
- `aggregate_incoming` works for any relationship type
- Works across all node labels
- Supports multiple aggregation types

**Generic Lookup:**
- `get_node_by_name` works for any label
- Extensible to other lookup methods

**Composability:**
- Tools can be chained: lookup → traverse → aggregate
- Results from one tool feed into another
- Enables complex multi-step queries

### ❌ DON'T: Create Hardcoded, Use-Case-Specific Tools

**Avoid:**
- `count_assets_in_hall`
- `count_assets_in_tank`
- `count_assets_in_reservoir`
- `list_assets_in_system`
- `find_location_by_name`

**Why:**
- Doesn't scale to new questions
- Code duplication
- Maintenance burden
- Inflexible

### Key Principles

1. **Separation of Concerns**
   - LLM handles reasoning
   - MCP handles database logic
   - Clear boundaries

2. **Composability > Hardcoded**
   - Generic tools can be combined
   - New questions don't require new tools
   - System evolves with graph structure

3. **Safety and Validation**
   - MCP validates all inputs
   - Prevents injection attacks
   - Enforces query limits
   - Handles errors gracefully

4. **Extensibility**
   - Easy to add new relationship types
   - Easy to add new aggregation types
   - Easy to add new node labels
   - Future-proof design

---

## Implementation Examples

### Example 1: Count Assets in Biofilter 11

**LLM Reasoning:**
1. "Biofilter 11" is a location
2. "items" refers to assets
3. Need to count assets located in Biofilter 11

**Tool Calls:**
```json
// Step 1: Find the location node
{
  "tool": "get_node_by_name",
  "parameters": {
    "label": "Location",
    "name": "Biofilter 11"
  }
}

// Step 2: Count assets in that location
{
  "tool": "aggregate_incoming",
  "parameters": {
    "start_node_id": "123",  // From step 1
    "relationship_types": ["LOCATED_IN"],
    "direction": "INCOMING",
    "target_label": "Asset",
    "aggregation": "count",
    "validity_filter": {
      "current_only": true
    }
  }
}
```

**Result:** `{"result": 15}`

---

### Example 2: List Assets in Hall 4

**Tool Calls:**
```json
// Step 1: Find Hall 4
{
  "tool": "get_node_by_name",
  "parameters": {
    "label": "Location",
    "name": "Hall 4"
  }
}

// Step 2: List assets
{
  "tool": "aggregate_incoming",
  "parameters": {
    "start_node_id": "456",
    "relationship_types": ["LOCATED_IN"],
    "direction": "INCOMING",
    "target_label": "Asset",
    "aggregation": "list",
    "include_attributes": ["name", "unique_id", "description"],
    "limit": 1000
  }
}
```

**Result:** List of asset objects

---

### Example 3: Count Assets in System

**Question:** "How many assets are in the Feeding System?"

**Tool Calls:**
```json
// Step 1: Find Feeding System
{
  "tool": "get_node_by_name",
  "parameters": {
    "label": "System",
    "name": "Feeding System"
  }
}

// Step 2: Count assets
{
  "tool": "aggregate_incoming",
  "parameters": {
    "start_node_id": "789",
    "relationship_types": ["PART_OF_SYSTEM"],
    "direction": "INCOMING",
    "target_label": "Asset",
    "aggregation": "count"
  }
}
```

---

### Example 4: Multi-Step Query

**Question:** "List all signals for assets in Tank 1"

**Tool Calls:**
```json
// Step 1: Find Tank 1
{
  "tool": "get_node_by_name",
  "parameters": {
    "label": "Location",
    "name": "Tank 1"
  }
}

// Step 2: Get assets in Tank 1
{
  "tool": "aggregate_incoming",
  "parameters": {
    "start_node_id": "111",
    "relationship_types": ["LOCATED_IN"],
    "direction": "INCOMING",
    "target_label": "Asset",
    "aggregation": "list",
    "include_attributes": ["node_id"]
  }
}

// Step 3: For each asset, get signals
// (Could be done in parallel or sequentially)
{
  "tool": "aggregate_incoming",
  "parameters": {
    "start_node_id": "222",  // Asset node_id from step 2
    "relationship_types": ["MEASURES"],
    "direction": "OUTGOING",
    "target_label": "Signal",
    "aggregation": "list"
  }
}
```

---

## Future Extensions

### 1. Semantic Search

**Tool:** `find_nodes_by_semantic_similarity`

Enables queries like:
- "Find locations similar to 'tank area'"
- "Find assets related to 'flow measurement'"

Uses embedding vectors stored in nodes.

---

### 2. GraphRAG Expansion

**Tool:** `expand_graph_context`

Retrieves related nodes for context expansion:
- Get neighboring nodes
- Get subgraph around a node
- Get hierarchical parents/children

---

### 3. Temporal Queries

**Enhanced:** `aggregate_incoming` with temporal support

Enables:
- "Count assets in Tank 1 as of 2023-06-01"
- "Show historical structure changes"
- "Find when an asset moved locations"

---

### 4. Multi-Relationship Traversal

**Enhanced:** Support for multiple relationship types in one traversal

Example:
```json
{
  "relationship_types": ["LOCATED_IN", "PART_OF_SYSTEM"],
  "direction": "BOTH",
  "target_label": "Asset"
}
```

---

### 5. Aggregation Options

**Enhanced:** More aggregation types
- `group_by`: Group results by attribute
- `distinct_count`: Count unique values
- `filter`: Apply filters before aggregation

---

### 6. Relationship Path Queries

**Tool:** `find_paths_between_nodes`

Finds shortest paths or all paths between nodes:
- "How is Tank 1 connected to Feeding System?"
- "What's the relationship chain from Aardal to Biofilter 11?"

---

## Security Considerations

### Input Validation

- Validate all node labels against allowed list
- Validate relationship types against schema
- Sanitize string inputs
- Enforce query limits (max nodes, max depth)

### Access Control

- Role-based access to different graph regions
- Filter results based on user permissions
- Audit logging of all queries

### Query Safety

- Prevent injection attacks
- Limit query complexity
- Timeout long-running queries
- Resource usage limits

---

## Performance Considerations

### Indexing

Ensure indexes on:
- `(label, name)` for node lookups
- `(relationship_type, validity_to)` for temporal queries
- `(label, embedding)` for semantic search

### Query Optimization

- Use parameterized queries
- Limit result sets
- Use appropriate Cypher patterns
- Cache frequently accessed nodes

### Scalability

- Handle large result sets with pagination
- Support parallel tool calls
- Optimize for common query patterns

---

## Summary

This documentation describes a **layered asset knowledge graph** and a **generic MCP tool interface** for natural language querying. The system:

1. **Encodes structure** using relationships in Neo4j
2. **Exposes generic tools** (`get_node_by_name`, `aggregate_incoming`) instead of hardcoded use cases
3. **Separates concerns** between LLM reasoning and database logic
4. **Scales** to new questions without creating new tools
5. **Supports** temporal queries, semantic search, and complex traversals

The design is **composable**, **extensible**, and **future-proof**, enabling the system to evolve with the graph structure while maintaining a clean, maintainable architecture.

---

## Appendix: Cypher Reference Patterns

### Node Lookup
```cypher
MATCH (n:Location {name: $name})
RETURN n
LIMIT 1
```

### Traversal with Validity
```cypher
MATCH (start)
WHERE id(start) = $start_id
MATCH (target:Asset)-[r:LOCATED_IN]->(start)
WHERE r.validity_to IS NULL
RETURN count(target)
```

### Temporal Traversal
```cypher
MATCH (start)
WHERE id(start) = $start_id
MATCH (target:Asset)-[r:LOCATED_IN]->(start)
WHERE r.validity_from <= $as_of_date
  AND (r.validity_to IS NULL OR r.validity_to >= $as_of_date)
RETURN target
```

### Multi-Relationship Traversal
```cypher
MATCH (start)
WHERE id(start) = $start_id
MATCH (target:Asset)-[r]->(start)
WHERE type(r) IN $relationship_types
  AND r.validity_to IS NULL
RETURN target
```

---

*Document Version: 1.0*  
*Last Updated: 2024*
