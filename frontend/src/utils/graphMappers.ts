import type { NodeWithColor, GraphResultNode, GraphResultRel } from '../types';
import type { Node, Relationship } from '@neo4j-nvl/base';
import { getColorForType } from '../constants';

// Common function to map Neo4j nodes into NVL nodes with color
export const mapGraphNodeToNvlNode = (node: GraphResultNode): NodeWithColor => {
  const id = node.id;
  const labels: string[] = node.labels || [];
  const nodeType = labels.length > 0 ? labels[0] : 'Unknown';
  const color = getColorForType(nodeType);
  return {
    id,
    caption: node.properties?.name as string,
    type: nodeType,
    color,
    properties: node.properties,
  };
};

export const mapGraphRelationshipToNvlRelationship = (
  rel: GraphResultRel
): Relationship => {
  return {
    id: String(rel.id),
    from: String(rel.from),
    to: String(rel.to),
    caption: rel.type,
  };
};
