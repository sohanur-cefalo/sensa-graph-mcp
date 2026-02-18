import type NVL from '@neo4j-nvl/base';
import { InteractiveNvlWrapper } from '@neo4j-nvl/react';
import type { Node, Relationship } from '@neo4j-nvl/base';
import WelcomeView from './WelcomeView';
import NodePropertiesPanel from './node-properties/NodePropertiesPanel';
import type { GraphResultNode, NodeWithColor } from '../types';

interface GraphCanvasProps {
  nodes: NodeWithColor[];
  relationships: Relationship[];
  nvlRef: React.RefObject<NVL | null>;
  loadAdjacent: (node: Node) => void;
  onNodeClick: (node: NodeWithColor | null) => void;
  selectedNode: NodeWithColor | null;
  updateNodeInGraph: (updatedNode: GraphResultNode) => void;
}

export default function GraphCanvas({
  nodes,
  relationships,
  nvlRef,
  loadAdjacent,
  onNodeClick,
  selectedNode,
  updateNodeInGraph,
}: GraphCanvasProps) {
  const isEmpty = nodes.length === 0 && relationships.length === 0;

  return (
    <div className="flex-1 min-h-0 flex flex-col md:flex-row gap-3 h-full">
      {/* left: graph canvas container */}
      <div className="flex-1 min-h-0 flex flex-col h-full">
        {/* bordered inner canvas */}
        <div className="flex-1 min-h-0 border border-[#e9f0f5] rounded-lg p-1 sm:p-2 mt-2 bg-[#fbfeff] overflow-hidden flex relative h-full">
          <div className="flex-1 min-h-0 w-full h-full">
            {isEmpty ? (
              <WelcomeView />
            ) : (
              <InteractiveNvlWrapper
                className="w-full h-full"
                ref={nvlRef}
                nvlOptions={{ initialZoom: 1 }}
                nodes={nodes}
                rels={relationships}
                mouseEventCallbacks={{
                  onZoom: true,
                  onPan: true,
                  onDrag: true,
                  onCanvasClick: () => onNodeClick(null),
                  onNodeDoubleClick: (node: Node) => loadAdjacent(node),
                  onNodeClick: (node: Node) =>
                    onNodeClick(node as NodeWithColor),
                }}
              />
            )}
          </div>
        </div>
      </div>

      {selectedNode && (
        <NodePropertiesPanel
          selectedNode={selectedNode}
          onClose={() => onNodeClick(null)}
          onNodeUpdate={updateNodeInGraph}
        />
      )}
    </div>
  );
}
