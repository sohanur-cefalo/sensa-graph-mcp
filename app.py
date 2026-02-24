"""
FastAPI server for Asset Graph RAG MCP tools.
Uses Claude to analyze queries and select appropriate tools.
"""

import inspect
import json
import os
import re
from typing import Any, Union, get_args, get_origin, Literal, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tools.count_breakdown import count_breakdown
from tools.count_by_category import count_by_category
from tools.count_by_label import count_by_label
from tools.count_nodes import count_nodes
from tools.count_related import count_related
from tools.count_related_by_name import count_related_by_name
from tools.find_node import find_node
from tools.list_related_by_name import list_related_by_name
from tools.get_node_connections import get_node_connections
from tools.get_schema import get_schema
from tools.list_related import list_related
from tools.list_categories import list_categories
from tools.run_query import run_query
from tools.query_influxdb import query_influxdb
from neo4j_config import get_driver, get_all_labels_from_db

load_dotenv()

# Initialize Anthropic client
claude_api_key = os.getenv("CLAUDE_API_KEY")
claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
max_response_length = int(os.getenv("MAX_RESPONSE_LENGTH", "0"))  # 0 means no truncation

if not claude_api_key:
    raise ValueError("CLAUDE_API_KEY not found in environment variables")

anthropic = Anthropic(api_key=claude_api_key)

# Initialize FastAPI app
app = FastAPI(
    title="Asset Graph RAG API",
    description="API for querying the Asset Graph knowledge graph via natural language",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tool registry: generic names for any knowledge graph (not project-specific)
TOOL_REGISTRY = {
    "find_node": find_node,
    "count_nodes": count_nodes,
    "count_by_label": count_by_label,
    "list_categories": list_categories,
    "get_node_connections": get_node_connections,
    "count_by_category": count_by_category,
    "count_related": count_related,
    "count_related_by_name": count_related_by_name,
    "list_related": list_related,
    "list_related_by_name": list_related_by_name,
    "count_breakdown": count_breakdown,
    "get_schema": get_schema,
    "run_query": run_query,
    "query_influxdb": query_influxdb,
}


def _to_json_serializable(obj: Any) -> Any:
    """Recursively convert Neo4j Node/Relationship and other non-JSON-serializable types for json.dumps."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_serializable(x) for x in obj]
    # Neo4j Node (has element_id and labels)
    if hasattr(obj, "element_id") and hasattr(obj, "labels"):
        return {
            "node_id": str(getattr(obj, "element_id", None) or getattr(obj, "id", "")),
            "labels": list(getattr(obj, "labels", [])),
            "properties": _to_json_serializable(dict(obj)),
        }
    # Neo4j Relationship (has element_id and type)
    if hasattr(obj, "element_id") and hasattr(obj, "type"):
        return {
            "relationship_id": str(getattr(obj, "element_id", "")),
            "type": str(getattr(obj, "type", "")),
            "start_node": _to_json_serializable(getattr(obj, "start_node", None)),
            "end_node": _to_json_serializable(getattr(obj, "end_node", None)),
            "properties": _to_json_serializable(dict(obj)),
        }
    # datetime / date
    if hasattr(obj, "isoformat") and callable(getattr(obj, "isoformat")):
        return obj.isoformat()
    # Neo4j Record or other mapping-like
    if hasattr(obj, "keys") and hasattr(obj, "__getitem__") and not isinstance(obj, type):
        try:
            return _to_json_serializable(dict(obj))
        except (TypeError, ValueError):
            pass
    return str(obj)


def python_type_to_json_schema(annotation: Any) -> dict[str, Any]:
    """Convert Python type annotation to JSON Schema."""
    if annotation == inspect.Parameter.empty:
        return {"type": "string"}
    
    # Handle Optional and Union types
    origin = get_origin(annotation)
    if origin is not None:
        if origin is Union:
            args = get_args(annotation)
            if args:
                # Filter out None types (for Optional[T] which is Union[T, None])
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    # Use the first non-None type
                    return python_type_to_json_schema(non_none_args[0])
        
        # Handle Literal types
        if origin is Literal:
            args = get_args(annotation)
            if args:
                # Extract string values from Literal
                enum_values = [str(arg) for arg in args]
                return {"type": "string", "enum": enum_values}
        
        # Handle list types
        if origin is list:
            args = get_args(annotation)
            items_schema = {"type": "string"}  # Default to string
            if args:
                items_schema = python_type_to_json_schema(args[0])
            return {"type": "array", "items": items_schema}
        
        # Handle dict types
        if origin is dict:
            return {"type": "object"}
    
    # Handle basic types (when origin is None, it's a concrete type)
    if annotation == str or annotation is str:
        return {"type": "string"}
    elif annotation == int or annotation is int:
        return {"type": "integer"}
    elif annotation == bool or annotation is bool:
        return {"type": "boolean"}
    elif annotation == float or annotation is float:
        return {"type": "number"}
    
    # Default to string for unknown types
    return {"type": "string"}


def get_tool_schemas() -> list[dict[str, Any]]:
    """Generate Anthropic tool schemas from registered tools."""
    schemas = []
    
    for tool_name, tool_func in TOOL_REGISTRY.items():
        sig = inspect.signature(tool_func)
        doc = tool_func.__doc__ or ""
        
        # Parse parameters
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            param_desc = f"Parameter {param_name}"
            
            # Convert Python type to JSON Schema
            json_schema = python_type_to_json_schema(param.annotation)
            
            # Add description
            json_schema["description"] = param_desc
            
            properties[param_name] = json_schema
            
            # Check if parameter is required (no default value)
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        schema = {
            "name": tool_name,
            "description": doc.strip(),
            "input_schema": {
                "type": "object",
                "properties": properties,
            },
        }
        
        # Only add required if there are required fields
        if required:
            schema["input_schema"]["required"] = required
        
        schemas.append(schema)
    
    return schemas


def truncate_response(text: str, max_length: int) -> str:
    """
    Truncate response text intelligently at sentence boundaries.
    If max_length is 0 or less, returns text as-is.
    """
    if max_length <= 0 or len(text) <= max_length:
        return text
    
    # Try to truncate at sentence boundaries
    truncated = text[:max_length]
    
    # Find the last sentence-ending punctuation before the truncation point
    sentence_endings = ['.', '!', '?', '\n']
    last_sentence_end = -1
    
    for i in range(len(truncated) - 1, max(0, len(truncated) - 200), -1):
        if truncated[i] in sentence_endings:
            # Check if it's followed by a space or end of string
            if i + 1 >= len(truncated) or truncated[i + 1] in [' ', '\n']:
                last_sentence_end = i + 1
                break
    
    if last_sentence_end > max_length * 0.8:  # Only use if we're not losing too much content
        truncated = truncated[:last_sentence_end].strip()
    else:
        # If no good sentence boundary found, truncate at word boundary
        last_space = truncated.rfind(' ', 0, max_length)
        if last_space > max_length * 0.8:
            truncated = truncated[:last_space].strip()
        else:
            truncated = truncated[:max_length].strip()
    
    # Add ellipsis if text was truncated
    if len(text) > len(truncated):
        truncated += "..."
    
    return truncated


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool with given arguments."""
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' not found"}
    
    tool_func = TOOL_REGISTRY[tool_name]
    
    try:
        # Get function signature to understand expected types
        sig = inspect.signature(tool_func)
        
        # Process and filter arguments
        processed_args = {}
        
        for param_name, param in sig.parameters.items():
            if param_name in arguments:
                value = arguments[param_name]
                
                # Get the expected type for this parameter
                param_annotation = param.annotation
                origin = get_origin(param_annotation)
                
                # Handle Optional types
                if origin is Union:
                    args = get_args(param_annotation)
                    non_none_args = [arg for arg in args if arg is not type(None)]
                    if non_none_args:
                        param_annotation = non_none_args[0]
                        origin = get_origin(param_annotation)
                
                # Special handling for known list parameters (like relationship_types)
                # This is a workaround for when Claude passes JSON strings instead of arrays
                if param_name in ["relationship_types"] and isinstance(value, str):
                    value_stripped = value.strip()
                    try:
                        parsed = json.loads(value_stripped)
                        if isinstance(parsed, list):
                            value = parsed
                    except (json.JSONDecodeError, ValueError):
                        # Fallback: try to extract array elements manually using regex
                        try:
                            import re
                            matches = re.findall(r'["\']([^"\']+)["\']', value_stripped)
                            if matches:
                                value = matches
                        except:
                            pass
                
                # Handle JSON string conversion for list/dict types
                # Check if parameter expects a list (including list[str], list[Any], etc.)
                elif origin is list:
                    # If value is a string, try to parse it as JSON
                    if isinstance(value, str):
                        value_stripped = value.strip()
                        try:
                            parsed = json.loads(value_stripped)
                            if isinstance(parsed, list):
                                value = parsed
                        except (json.JSONDecodeError, ValueError):
                            # Fallback: try to extract array elements manually using regex
                            try:
                                import re
                                # Extract quoted strings from array-like string
                                # Handles both "[\"LOCATED_IN\"]" and '["LOCATED_IN"]'
                                matches = re.findall(r'["\']([^"\']+)["\']', value_stripped)
                                if matches:
                                    value = matches
                            except:
                                pass  # Keep original value if all parsing fails
                    
                    # If value is not a list but we expect one, try to convert
                    elif not isinstance(value, list):
                        # Try to parse as JSON if it's a string-like object
                        if hasattr(value, '__str__'):
                            try:
                                value_str = str(value).strip()
                                if value_str.startswith('['):
                                    parsed = json.loads(value_str)
                                    if isinstance(parsed, list):
                                        value = parsed
                            except:
                                pass
                
                # Check if parameter expects a dict
                elif origin is dict:
                    # Always try to parse as JSON object if it's a string
                    if isinstance(value, str):
                        value_stripped = value.strip()
                        try:
                            parsed = json.loads(value_stripped)
                            if isinstance(parsed, dict):
                                value = parsed
                        except (json.JSONDecodeError, ValueError):
                            pass  # Keep original value if parsing fails
                
                processed_args[param_name] = value
        
        result = tool_func(**processed_args)
        return result
    except Exception as e:
        import traceback
        return {"error": f"Error executing tool: {str(e)}\n{traceback.format_exc()}"}


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str
    model: Optional[str] = None  # Override CLAUDE_MODEL for this request (e.g. benchmarking)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Asset Graph RAG API",
        "version": "1.0.0",
        "available_tools": list(TOOL_REGISTRY.keys()),
    }


@app.get("/tools")
async def list_tools():
    """List all available tools with their schemas."""
    return {"tools": get_tool_schemas()}


@app.get("/graph/entity-types")
async def get_entity_types():
    """Get all entity types (node labels) from Neo4j."""
    try:
        labels = list(get_all_labels_from_db())
        return {"entity_types": sorted(labels)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching entity types: {str(e)}")


@app.post("/graph/reset")
async def reset_graph():
    """Reset the graph by deleting all nodes and relationships."""
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as deleted")
            deleted = result.single()["deleted"] if result.single() else 0
        
        # Clear cached labels since graph was reset
        import neo4j_config
        neo4j_config._allowed_labels = None
        neo4j_config._get_node_by_name_labels = None
        
        return {"message": "Graph reset successfully", "nodes_deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting graph: {str(e)}")


@app.get("/graph")
async def get_graph(limit: int = 50):
    """Get graph data (nodes and relationships) from Neo4j."""
    try:
        driver = get_driver()
        nodes = []
        relationships = []
        
        with driver.session() as session:
            # Fetch nodes
            node_query = f"""
            MATCH (n)
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            LIMIT $limit
            """
            node_result = session.run(node_query, limit=limit)
            for record in node_result:
                nodes.append({
                    "id": record["id"],
                    "labels": list(record["labels"]),
                    "properties": dict(record["properties"])
                })
            
            # Fetch relationships for the nodes we fetched
            if nodes:
                node_ids = [node["id"] for node in nodes]
                rel_query = """
                MATCH (a)-[r]->(b)
                WHERE elementId(a) IN $node_ids AND elementId(b) IN $node_ids
                RETURN elementId(r) AS id, elementId(a) AS from, elementId(b) AS to, 
                       type(r) AS type, properties(r) AS properties
                LIMIT $limit
                """
                rel_result = session.run(rel_query, node_ids=node_ids, limit=limit)
                for record in rel_result:
                    relationships.append({
                        "id": record["id"],
                        "from": record["from"],
                        "to": record["to"],
                        "type": record["type"],
                        "properties": dict(record["properties"])
                    })
        
        return {"nodes": nodes, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching graph: {str(e)}")


@app.get("/graph/entities/{entity_type}")
async def get_entities_by_type(entity_type: str, limit: int = 50):
    """Get entities of a specific type from Neo4j."""
    try:
        driver = get_driver()
        nodes = []
        relationships = []
        
        with driver.session() as session:
            # Fetch nodes of the specified type
            node_query = f"""
            MATCH (n:{entity_type})
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            LIMIT $limit
            """
            node_result = session.run(node_query, limit=limit)
            for record in node_result:
                nodes.append({
                    "id": record["id"],
                    "labels": list(record["labels"]),
                    "properties": dict(record["properties"])
                })
            
            # Fetch relationships for these nodes
            if nodes:
                node_ids = [node["id"] for node in nodes]
                rel_query = """
                MATCH (a)-[r]->(b)
                WHERE elementId(a) IN $node_ids AND elementId(b) IN $node_ids
                RETURN elementId(r) AS id, elementId(a) AS from, elementId(b) AS to, 
                       type(r) AS type, properties(r) AS properties
                LIMIT $limit
                """
                rel_result = session.run(rel_query, node_ids=node_ids, limit=limit)
                for record in rel_result:
                    relationships.append({
                        "id": record["id"],
                        "from": record["from"],
                        "to": record["to"],
                        "type": record["type"],
                        "properties": dict(record["properties"])
                    })
        
        return {"nodes": nodes, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching entities: {str(e)}")


@app.get("/graph/adjacent/{node_id}")
async def get_adjacent_nodes(node_id: str, limit: int = 50):
    """Get adjacent nodes and relationships for a given node."""
    try:
        driver = get_driver()
        nodes = []
        relationships = []
        node_ids_set = {node_id}
        
        with driver.session() as session:
            # Fetch the starting node
            start_query = """
            MATCH (n)
            WHERE elementId(n) = $node_id
            RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties
            """
            start_result = session.run(start_query, node_id=node_id)
            start_record = start_result.single()
            if start_record:
                nodes.append({
                    "id": start_record["id"],
                    "labels": list(start_record["labels"]),
                    "properties": dict(start_record["properties"])
                })
            
            # Fetch adjacent nodes and relationships
            adj_query = """
            MATCH (start)-[r]-(adj)
            WHERE elementId(start) = $node_id
            RETURN elementId(adj) AS id, labels(adj) AS labels, properties(adj) AS properties,
                   elementId(r) AS rel_id, elementId(start) AS from_id, elementId(adj) AS to_id,
                   type(r) AS rel_type, properties(r) AS rel_properties
            LIMIT $limit
            """
            adj_result = session.run(adj_query, node_id=node_id, limit=limit)
            for record in adj_result:
                adj_id = record["id"]
                node_ids_set.add(adj_id)
                
                # Add adjacent node if not already added
                if not any(n["id"] == adj_id for n in nodes):
                    nodes.append({
                        "id": adj_id,
                        "labels": list(record["labels"]),
                        "properties": dict(record["properties"])
                    })
                
                # Add relationship
                relationships.append({
                    "id": record["rel_id"],
                    "from": record["from_id"],
                    "to": record["to_id"],
                    "type": record["rel_type"],
                    "properties": dict(record["rel_properties"])
                })
        
        return {"nodes": nodes, "relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching adjacent nodes: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that uses Claude to analyze the query and select appropriate tools.
    
    The LLM will:
    1. Analyze the natural language query
    2. Select which tools to call
    3. Determine arguments for each tool
    4. Execute the tools
    5. Summarize the results
    """
    query = request.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    effective_model = request.model or claude_model
    
    # Get tool schemas
    tools = get_tool_schemas()
    
    # System message explaining the task
    system_message = """You are an assistant that helps users query an asset knowledge graph stored in Neo4j.

Your job is to:
1. Analyze the user's natural language query
2. Select the appropriate tool(s) to answer the query
3. Provide the correct arguments for each tool
4. If a tool call fails or returns no results, try different approaches (different tools, different parameters like name_match="prefix" instead of "exact", etc.)
5. Continue trying until you find a successful answer or exhaust reasonable options
6. After tools are executed successfully, summarize the results in a clear, natural language response

Available tools (generic names for any knowledge graph):
- find_node: Find (first) node with a given name; returns node_id, label, attributes for count_related/list_related.
- count_nodes: Count nodes with a given name (exact match).
- count_by_label: Count all nodes with a given label (e.g., "Asset", "Location").
- list_categories: List category nodes and their hierarchy.
- get_node_connections: Show how a node is connected (incoming/outgoing relationships).
- count_by_category: Count entities per category (location/system or other dimensions).
- count_related_by_name: For "how many entities in X" (e.g. assets in Biofilter 11): finds ALL nodes named X, counts related entities (e.g. Asset with LOCATED_IN) per node, returns total_count and per-node breakdown. Prefer this for count-in-location questions.
- list_related_by_name: Same but lists the related entities (finds all nodes by name, then lists related per node). Use for "list assets in X".
- count_related: Count related to a single node (use node_id from find_node). Use when you already have one node_id.
- list_related: List related to a single node (use node_id from find_node).
- count_breakdown: Full breakdown of entity counts per container/dimension (Location, System, Context)
- get_schema: Introspect graph structure (labels, relationship types, property keys). Use when you need to understand the schema to answer a question or when domain tools are insufficient.
- run_query: Execute a read-only query (e.g. Cypher: MATCH, RETURN). Use only when domain tools cannot answer the question. Writes and schema changes are rejected. Optional argument: limit (default 1000).
- query_influxdb: Query time-series data from InfluxDB (e.g. flow, capacity, temperature). Use for: "last 7 days trend of flow", "capacity for last week", "flow for Hall 1". Either location_name or signal_name is required; signal name matching is case-insensitive. Args: location_name (optional), signal_name (optional but required if no location; e.g. "capacity", "Flow"), natural_query, time_range (always include the unit, e.g. "7 days", "24 hours" — not just "7"), limit.

Important guidelines:
- For "how many entities in X" (e.g. "Count the number of assets in Biofilter 11"): use count_related_by_name(name=X, relationship_types=["LOCATED_IN"], target_label="Asset"). It finds all nodes named X, counts assets per node, and returns the total. For "list items in X" use list_related_by_name with the same parameters. Use relationship_types and target_label appropriate to the graph.
- IMPORTANT: When passing array parameters (like relationship_types), pass them as actual arrays, NOT as JSON strings. For example: relationship_types=["LOCATED_IN"] not relationship_types='["LOCATED_IN"]'
- For generic or plural names (e.g. "biofilters", "halls"), call find_node with the base name (e.g. name="Biofilter", name="Hall"); if not found, try other names or get_node_connections to explore.
- For "where is X" or "where are X", use find_node then get_node_connections on the node name (or on nodes[0] if a single node) to see hierarchy.
- count_breakdown: use container_type="Context" if the graph uses Context for places when container_type="Location" returns empty; "Both" includes Location, System, and Context.
- If find_node returns "found": false or nodes is empty, try a different name or get_node_connections on a related node.
- Prefer the domain tools above; use get_schema when you need labels/relationship types, and run_query only when the question cannot be answered with other tools. The database is read-only.
- For time-series questions (flow trend, capacity, last N days): use query_influxdb with either location_name and/or signal_name (e.g. "capacity", "Flow"; matching is case-insensitive), natural_query, time_range (e.g. "7 days" — always include the unit). Location is optional when signal_name is provided. When presenting results, if the response includes requested_time_range, state that the query was for that range (e.g. "last 7 days from current date"); then give the actual data range (time_range in the response) and the summary so the user understands what was requested vs what data was returned.
- Only provide a final answer when you have successfully found results. If all attempts fail, explain what you tried and why it didn't work.
- Always provide clear, helpful summaries of the results
- Do NOT output planning or partial responses like "Let me check..." or "I'll look into that..." as your only response. Either call the appropriate tool(s) first (in the same turn, without such preamble), or after you have tool results, output only the final summary. Never respond with only a sentence that says you will check something without actually calling tools."""
    
    # Initialize conversation history and tracking
    conversation_messages = [
        {
            "role": "user",
            "content": query,
        }
    ]
    
    all_tool_calls = []
    all_tool_results = []
    max_iterations = 5  # Maximum number of tool-calling iterations
    iteration = 0
    
    # Retry loop: continue until we get a successful result or max iterations
    while iteration < max_iterations:
        iteration += 1
        
        try:
            # Call Claude to select tools or provide final answer
            message = anthropic.messages.create(
                model=effective_model,
                max_tokens=4096,
                system=system_message,
                messages=conversation_messages,
                tools=tools,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calling Claude API: {str(e)}"
            )
        
        # Check if Claude provided a text answer (no more tools needed)
        text_response = ""
        tool_use_blocks = []
        
        for content in message.content:
            if hasattr(content, "type"):
                if content.type == "text":
                    text_response = content.text
                elif content.type == "tool_use":
                    tool_use_blocks.append(content)
        
        # If Claude provided a text answer, we're done (unless it's planning text with no tools run yet)
        if text_response and not tool_use_blocks:
            # Reject planning-style responses when no tools have been executed yet
            planning_phrases = (
                r"let me (check|look|find|examine|see|get)",
                r"now let me",
                r"I'll (check|look|find|examine)",
                r"I will (check|look|find|examine)",
                r"by examining (their |the )?connections",
                r"examining their connections",
            )
            is_planning = any(
                re.search(p, text_response, re.IGNORECASE) for p in planning_phrases
            )
            if len(all_tool_calls) == 0 and is_planning:
                # Model returned planning text without calling tools; prompt it to continue
                conversation_messages.append({
                    "role": "assistant",
                    "content": message.content,
                })
                conversation_messages.append({
                    "role": "user",
                    "content": "Continue. Call the appropriate tool(s) to answer the question, then provide your final answer. Do not output only planning or partial responses.",
                })
                continue
            # Genuine final answer
            conversation_messages.append({
                "role": "assistant",
                "content": message.content,
            })
            truncated_response = truncate_response(text_response, max_response_length)
            return ChatResponse(
                response=truncated_response,
                tool_calls=all_tool_calls,
                tool_results=all_tool_results,
            )
        
        # If no tools were called and no text response, we're done
        if not tool_use_blocks:
            break
        
        # Execute tools
        tool_result_blocks = []
        iteration_tool_calls = []
        iteration_tool_results = []
        
        for tool_use in tool_use_blocks:
            iteration_tool_calls.append({
                "tool_name": tool_use.name,
                "arguments": tool_use.input,
            })
            
            # Execute the tool
            result = execute_tool(tool_use.name, tool_use.input)
            result_serializable = _to_json_serializable(result)
            
            iteration_tool_results.append({
                "tool_name": tool_use.name,
                "result": result_serializable,
            })
            
            # Build tool result block for Claude
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(result_serializable),
            })
        
        # Add to overall tracking
        all_tool_calls.extend(iteration_tool_calls)
        all_tool_results.extend(iteration_tool_results)
        
        # Check if we got successful results
        has_successful_result = False
        for result in iteration_tool_results:
            tool_result = result["result"]
            # Check for success indicators
            if isinstance(tool_result, dict):
                # Check for various success indicators
                if tool_result.get("found") is True:
                    has_successful_result = True
                    break
                if tool_result.get("total_count", 0) > 0:
                    has_successful_result = True
                    break
                if tool_result.get("total_result", 0) > 0:
                    has_successful_result = True
                    break
                if tool_result.get("result") and not tool_result.get("error"):
                    # Check if result is a non-empty list or positive number
                    result_value = tool_result.get("result")
                    if isinstance(result_value, list) and len(result_value) > 0:
                        has_successful_result = True
                        break
                    if isinstance(result_value, (int, float)) and result_value > 0:
                        has_successful_result = True
                        break
                # Check for per_node results
                if tool_result.get("per_node") and len(tool_result.get("per_node", [])) > 0:
                    has_successful_result = True
                    break
                # Check for categories or other data
                if tool_result.get("categories") and len(tool_result.get("categories", [])) > 0:
                    has_successful_result = True
                    break
                # get_schema: success when schema summary is present
                if tool_result.get("summary"):
                    has_successful_result = True
                    break
                # run_query: success when no error (even if result list is empty)
                if "result" in tool_result and not tool_result.get("error"):
                    has_successful_result = True
                    break
        
        # Add assistant's tool use to conversation
        conversation_messages.append({
            "role": "assistant",
            "content": message.content,
        })
        
        # Add tool results to conversation
        conversation_messages.append({
            "role": "user",
            "content": tool_result_blocks,
        })
        
        # If we have successful results, ask Claude for final answer (or more tool calls)
        if has_successful_result:
            try:
                final_message = anthropic.messages.create(
                    model=effective_model,
                    max_tokens=4096,
                    system=system_message,
                    messages=conversation_messages,
                    tools=tools,
                )
                final_text = ""
                final_tool_use_blocks = []
                for content in final_message.content:
                    if hasattr(content, "type"):
                        if content.type == "text":
                            final_text = content.text
                        elif content.type == "tool_use":
                            final_tool_use_blocks.append(content)
                # If model requested more tools (e.g. to fetch sensors), run them and continue loop
                if final_tool_use_blocks:
                    conversation_messages.append({
                        "role": "assistant",
                        "content": final_message.content,
                    })
                    more_tool_result_blocks = []
                    for tool_use in final_tool_use_blocks:
                        result = execute_tool(tool_use.name, tool_use.input)
                        result_serializable = _to_json_serializable(result)
                        all_tool_calls.append({"tool_name": tool_use.name, "arguments": tool_use.input})
                        all_tool_results.append({"tool_name": tool_use.name, "result": result_serializable})
                        more_tool_result_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": json.dumps(result_serializable),
                        })
                    conversation_messages.append({
                        "role": "user",
                        "content": more_tool_result_blocks,
                    })
                    continue
                # Genuine final text answer
                if final_text:
                    is_planning = any(
                        re.search(p, final_text, re.IGNORECASE)
                        for p in (
                            r"let me (check|look|find|examine|see|get)",
                            r"now let me",
                            r"I'll (check|look|find|examine)",
                            r"examining their connections",
                        )
                    )
                    if not is_planning:
                        truncated_answer = truncate_response(final_text, max_response_length)
                        return ChatResponse(
                            response=truncated_answer,
                            tool_calls=all_tool_calls,
                            tool_results=all_tool_results,
                        )
            except Exception as e:
                pass
        
        # If no successful results and we've hit max iterations, break
        if iteration >= max_iterations:
            break
    
    # If we exit the loop without a final answer, get one from Claude
    try:
        final_message = anthropic.messages.create(
            model=effective_model,
            max_tokens=4096,
            system=system_message,
            messages=conversation_messages,
        )
        
        answer = ""
        for content in final_message.content:
            if hasattr(content, "type") and content.type == "text":
                answer = content.text
            elif hasattr(content, "text"):
                answer = content.text
        
        if not answer:
            answer = f"I tried {len(all_tool_calls)} tool call(s) but couldn't find the requested information. Here's what I attempted:\n\n{json.dumps(all_tool_calls, indent=2)}"
    except Exception as e:
        answer = f"I tried {len(all_tool_calls)} tool call(s) but encountered an error: {str(e)}"
    
    # Truncate response if max_response_length is set
    truncated_answer = truncate_response(answer, max_response_length)
    
    return ChatResponse(
        response=truncated_answer,
        tool_calls=all_tool_calls,
        tool_results=all_tool_results,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
