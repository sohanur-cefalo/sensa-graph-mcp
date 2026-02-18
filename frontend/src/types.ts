import type { Node, NVL, Relationship } from '@neo4j-nvl/base';
export interface JsonEntity {
  id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface JsonRelationship {
  source_id: string;
  target_id: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface ChatApiResponse {
  query: string;
  response: string;
  entityRelationships?: {
    entities: GraphResultNode[];
    relationships: GraphResultRel[];
  };
}

export interface GraphResultNode {
  id: string;
  labels: string[];
  properties: Record<string, unknown>;
}

export interface GraphResultRel {
  id: string;
  from: string;
  to: string;
  type: string;
  properties: Record<string, unknown>;
}

export type NodeWithColor = Node & {
  type: string;
  color: string;
  caption: string;
  properties: Record<string, unknown>;
};

export type GraphData = {
  nodes: GraphResultNode[];
  relationships: GraphResultRel[];
};

export type GraphController = {
  nodes: NodeWithColor[];
  relationships: Relationship[];
  nvlRef: React.RefObject<NVL | null>;
  selectedNode: NodeWithColor | null;
  loadGraph: () => Promise<void>;
  resetGraph: () => Promise<void>;
  loadAdjacent: (node: Node) => Promise<void>;
  loadEntitiesByType: (entityType: string) => Promise<void>;
  selectNode: (node: NodeWithColor | null) => void;
  applyGraphData: (
    nodes: GraphResultNode[],
    relationships: GraphResultRel[]
  ) => void;
  updateNodeInGraph: (updatedNode: GraphResultNode) => void;
};

export type ResizableWidthController = {
  width: number;
  beginResize: (clientX: number) => void;
  resizeTo: (clientX: number) => void;
};
