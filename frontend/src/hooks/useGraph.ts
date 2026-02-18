import { useState, useRef } from 'react';
import type { Node, Relationship } from '@neo4j-nvl/base';
import type NVL from '@neo4j-nvl/base';
import {
  fetchGraph,
  fetchAdjacent,
  fetchEntitiesByType,
} from '../graph/graphService';
import {
  mapGraphNodeToNvlNode,
  mapGraphRelationshipToNvlRelationship,
} from '../utils/graphMappers';
import type {
  NodeWithColor,
  GraphController,
  GraphResultNode,
  GraphResultRel,
} from '../types';
import { DEFAULT_FETCH_LIMIT } from '../constants';

export function useGraph(): GraphController {
  const [nodes, setNodes] = useState<NodeWithColor[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [selectedNode, setSelectedNode] = useState<NodeWithColor | null>(null);

  const nvlRef = useRef<NVL | null>(null);

  const loadGraph = async () => {
    try {
      const data = await fetchGraph(DEFAULT_FETCH_LIMIT);
      if (data.nodes.length === 0 && data.relationships.length === 0) {
        alert('No node and relationship found in the database.');
      }
      setNodes(data.nodes.map(mapGraphNodeToNvlNode));
      setRelationships(
        data.relationships.map(mapGraphRelationshipToNvlRelationship)
      );
    } catch (err) {
      console.error(err);
      alert('Failed to load graph');
    }
  };

  const resetGraph = async () => {
    try {
      // Use relative URL for proxy (ngrok) or absolute for direct connection
      const runtimeEnv = (import.meta as any).env;
      const apiUrl = runtimeEnv?.VITE_API_URL || runtimeEnv?.VITE_API_BASE_URL;
      const apiBase = (apiUrl && !apiUrl.includes('localhost') && !apiUrl.includes('127.0.0.1')) 
        ? apiUrl 
        : '';
      const response = await fetch(`${apiBase}/graph/reset`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`Failed to reset graph: ${response.statusText}`);
      }
      // Clear local state after successful API call
      setNodes([]);
      setRelationships([]);
      setSelectedNode(null);
    } catch (err) {
      console.error('Error resetting graph:', err);
      alert('Failed to reset graph. Please try again.');
    }
  };

  const loadAdjacent = async (node: Node) => {
    try {
      const data = await fetchAdjacent(node.id, DEFAULT_FETCH_LIMIT);

      setNodes((prev) => {
        const existing = new Set(prev.map((n) => n.id));
        const newMapped = data.nodes
          .filter((n) => !existing.has(n.id))
          .map(mapGraphNodeToNvlNode);

        return [...prev, ...newMapped];
      });

      setRelationships((prev) => {
        const existing = new Set(prev.map((r) => r.id));
        const newRels = data.relationships
          .filter((r) => !existing.has(r.id))
          .map(mapGraphRelationshipToNvlRelationship);

        return [...prev, ...newRels];
      });

      const neighborIds = data.nodes.map((n) => n.id);
      const idsToFit = Array.from(new Set([node.id, ...neighborIds]));
      nvlRef.current?.fit?.(idsToFit);
    } catch (err) {
      console.error(err);
      alert('Failed to load adjacent nodes');
    }
  };

  const loadEntitiesByType = async (entityType: string) => {
    try {
      const data = await fetchEntitiesByType(entityType, DEFAULT_FETCH_LIMIT);

      if (data.nodes.length === 0) {
        alert(`No entities of type "${entityType}" found in the database.`);
        return;
      }

      setNodes(data.nodes.map(mapGraphNodeToNvlNode));
      setSelectedNode(null);

      if (data.nodes.length > 0) {
        const nodeIds = data.nodes.map((n) => n.id);
        nvlRef.current?.fit?.(nodeIds);
      }
    } catch (err) {
      console.error(err);
      alert(`Failed to load entities of type "${entityType}"`);
    }
  };

  const selectNode = (node: NodeWithColor | null) => {
    setSelectedNode(node);
  };

  function applyGraphData(
    entities: GraphResultNode[],
    relationships: GraphResultRel[]
  ) {
    const newNodes = entities.map(mapGraphNodeToNvlNode);
    const newRels = relationships.map(mapGraphRelationshipToNvlRelationship);
    setNodes(newNodes);
    setRelationships(newRels);

    if (newNodes.length > 0) {
      setTimeout(() => {
        try {
          const nodeIds = newNodes.map((node) => node.id);
          nvlRef.current?.fit?.(nodeIds);
        } catch (err) {
          console.log(err);
        }
      }, 100);
    }
  }

  const updateNodeInGraph = (updatedNode: GraphResultNode) => {
    const mappedNode = mapGraphNodeToNvlNode(updatedNode);

    setNodes((prev) =>
      prev.map((node) => (node.id === updatedNode.id ? mappedNode : node))
    );

    if (selectedNode?.id === updatedNode.id) {
      setSelectedNode(mappedNode);
    }
  };

  return {
    nodes,
    relationships,
    nvlRef,
    selectedNode,

    loadGraph,
    resetGraph,
    loadAdjacent,
    loadEntitiesByType,
    selectNode,
    applyGraphData,
    updateNodeInGraph,
  };
}
