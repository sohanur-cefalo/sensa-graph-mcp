import type { GraphData, GraphResultNode } from '../types';

// Get API base URL - use relative URL for proxy (ngrok) or absolute for direct connection
const getApiBaseUrl = (): string => {
  const runtimeEnv = (import.meta as any).env;
  // If VITE_API_URL is set and not localhost, use it (for production)
  const apiUrl = runtimeEnv?.VITE_API_URL || runtimeEnv?.VITE_API_BASE_URL;
  if (apiUrl && !apiUrl.includes('localhost') && !apiUrl.includes('127.0.0.1')) {
    return apiUrl;
  }
  // Otherwise use relative URL (works with Vite proxy for ngrok)
  return '';
};

export async function fetchGraph(limit: number): Promise<GraphData> {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(`${apiBase}/graph?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching graph:', error);
    throw error;
  }
}

export async function fetchAdjacent(
  nodeElementId: string,
  limit: number
): Promise<GraphData> {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(
      `${apiBase}/graph/adjacent/${encodeURIComponent(
        nodeElementId
      )}?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error fetching adjacent nodes for ${nodeElementId}:`, error);
    throw error;
  }
}

export async function fetchEntitiesByType(
  entityType: string,
  limit: number
): Promise<GraphData> {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(
      `${apiBase}/graph/entities/${encodeURIComponent(
        entityType
      )}?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error fetching entities for type ${entityType}:`, error);
    throw error;
  }
}

export async function updateNodeProperties(
  nodeId: string,
  properties: Record<string, any>,
  deleteProperties: string[] = []
): Promise<GraphResultNode> {
  try {
    const apiBase = getApiBaseUrl();
    const response = await fetch(
      `${apiBase}/graph/nodes/${encodeURIComponent(nodeId)}/properties`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          node_id: nodeId,
          properties,
          delete_properties: deleteProperties,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error updating node properties for ${nodeId}:`, error);
    if (error instanceof TypeError) {
      throw new Error('Failed to update node properties. Please ensure the backend server is running.');
    }
    
    throw error;
  }
}
