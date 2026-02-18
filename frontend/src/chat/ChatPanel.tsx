import { useChat } from '../hooks/useChat';
import { useEffect } from 'react';
import { ChatHeader } from './ChatHeader';
import { ConversationView } from './ConversationView';
import { ChatInput } from './ChatInput';
import type { GraphResultNode, GraphResultRel } from '../types';

type ChatPanelProps = {
  width: number;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  onSubgraphReceived: (
    entities: GraphResultNode[],
    relationships: GraphResultRel[]
  ) => void;
};

export default function ChatPanel({
  width,
  isCollapsed = false,
  onToggleCollapse,
  onSubgraphReceived,
}: ChatPanelProps) {
  const {
    messages,
    input,
    isLoading,
    messagesRef,
    setInput,
    sendMessage,
    handleEnter,
    graphData,
    clearMessages,
  } = useChat();

  useEffect(() => {
    if (graphData) {
      onSubgraphReceived(graphData.nodes, graphData.relationships);
    }
  }, [graphData]);

  return (
    <div
      className="h-full flex flex-col md:border-l border-[#eef4f8] w-full md:w-auto relative"
      style={width > 0 ? { width } : undefined}
    >
      <ChatHeader 
        onClear={clearMessages}
        onToggleCollapse={onToggleCollapse}
      />

      <ConversationView messages={messages} messagesRef={messagesRef} />

      <ChatInput
        input={input}
        isLoading={isLoading}
        setInput={setInput}
        sendMessage={sendMessage}
        handleEnter={handleEnter}
      />
    </div>
  );
}
