"""
Example usage of the FastAPI /chat endpoint.

This demonstrates how to call the API from a frontend or other client.
The /chat endpoint accepts natural language queries and uses Claude to select and execute tools.
"""

import requests
import json

# Base URL of the API
BASE_URL = "http://localhost:8000"


def example_natural_language_query():
    """Example: Ask a natural language question."""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "query": "How many assets are there in total?"
        }
    )
    print("Natural language query:")
    print(json.dumps(response.json(), indent=2))


def example_count_query():
    """Example: Count query."""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "query": "How many assets are in Hall 1?"
        }
    )
    print("\nCount query:")
    print(json.dumps(response.json(), indent=2))


def example_list_query():
    """Example: List query."""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "query": "What assets are in Biofilter 11?"
        }
    )
    print("\nList query:")
    print(json.dumps(response.json(), indent=2))


def example_list_tools():
    """Example: List all available tools."""
    response = requests.get(f"{BASE_URL}/tools")
    print("\nAvailable tools:")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    print("FastAPI Asset Graph RAG API Examples\n")
    print("=" * 50)
    
    # Make sure the server is running before running these examples
    try:
        example_list_tools()
        example_single_tool_call()
        example_multiple_tool_calls()
        example_alternative_endpoint()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API.")
        print("Make sure the server is running:")
        print("  python run_server.py")
        print("  or")
        print("  uvicorn app:app --reload")
