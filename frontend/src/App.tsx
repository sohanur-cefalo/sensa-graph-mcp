import React, { useState } from 'react';
import { useGraph } from './hooks/useGraph';

import LoadFromNeo4jButton from './graph/graph-controls/LoadFromNeo4jButton';
import ChatPanel from './chat/ChatPanel';
import EntityTypesView from './graph/graph-controls/EntityTypesView';
import GraphCanvas from './graph/GraphCanvas';
import { VerticalResizer } from './vertical-resizer/VerticalResizer';
import { useResizableWidth } from './hooks/useResizableWidth';

import {
  CHAT_DEFAULT_WIDTH,
  CHAT_MIN_WIDTH,
  CHAT_MAX_WIDTH,
} from './constants';

export function App(): React.JSX.Element {
  const graphController = useGraph();
  const [isChatCollapsed, setIsChatCollapsed] = useState(false);

  const { width, beginResize, resizeTo } = useResizableWidth(
    CHAT_DEFAULT_WIDTH,
    CHAT_MIN_WIDTH,
    CHAT_MAX_WIDTH
  );

  return (
    <div className="w-full h-screen p-2 sm:p-4 box-border bg-[#f6f8fa]">
      <div className="h-full flex flex-col border border-[#e6edf2] rounded-[10px] p-2 sm:p-3 bg-white shadow-[0_6px_18px_rgba(15,23,42,0.06)]">
        <div className="flex items-start gap-2 mb-2">
          <LoadFromNeo4jButton onClick={graphController.loadGraph} />
        </div>
        <EntityTypesView
          onEntityTypeClick={graphController.loadEntitiesByType}
        />
        <div className="flex-1 min-h-0 flex flex-col md:flex-row gap-0 md:gap-3">
          {/* Graph Canvas */}
          <div className="order-2 md:order-1 flex-1 min-h-0 flex flex-col relative z-0">
            <GraphCanvas
              nodes={graphController.nodes}
              relationships={graphController.relationships}
              nvlRef={graphController.nvlRef}
              loadAdjacent={graphController.loadAdjacent}
              onNodeClick={(node) => graphController.selectNode(node)}
              selectedNode={graphController.selectedNode}
              updateNodeInGraph={graphController.updateNodeInGraph}
            />
          </div>

          {/* Chat Panel with integrated resizer - Show first on mobile, second on desktop */}
          {!isChatCollapsed && (
            <div className="order-1 md:order-3 flex-1 min-h-0 flex flex-col md:flex-none relative group">
              {/* Resizer attached to left edge of chat panel */}
              <div className="absolute left-0 top-0 bottom-0 z-10 flex items-center pointer-events-auto">
                <VerticalResizer onBegin={beginResize} onDrag={resizeTo} />
              </div>
              <ChatPanel
                width={width}
                isCollapsed={isChatCollapsed}
                onToggleCollapse={() => setIsChatCollapsed(!isChatCollapsed)}
                onSubgraphReceived={(entities, relationships) =>
                  graphController.applyGraphData(entities, relationships)
                }
              />
            </div>
          )}

          {/* Collapsed chat button - Show when chat is collapsed */}
          {isChatCollapsed && (
            <button
              onClick={() => setIsChatCollapsed(false)}
              className="fixed right-4 bottom-4 md:relative md:right-auto md:bottom-auto order-1 md:order-3 z-50 px-4 py-3 bg-[#0f62ff] text-white rounded-full shadow-lg hover:bg-[#0a4fcc] active:bg-[#0940a3] transition-colors touch-manipulation"
              aria-label="Show chat"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
