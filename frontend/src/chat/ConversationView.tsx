import { ChatMessage } from './ChatMessage';
import type { ChatMessageType } from '../hooks/useChat';

type ConversationViewProps = {
  messages: ChatMessageType[];
  messagesRef: React.RefObject<HTMLDivElement | null>;
};

export function ConversationView({
  messages,
  messagesRef,
}: ConversationViewProps) {
  return (
    <div
      ref={messagesRef}
      className="flex-1 min-h-0 overflow-auto p-2 sm:p-3 space-y-1 bg-linear-to-b from-transparent to-[#fbfdff]"
    >
      {messages.length === 0 && (
        <div className="text-sm sm:text-sm text-[#566171] mt-4 px-1">
          Start the chat by typing a message below.
        </div>
      )}

      {messages.map((m, idx) => (
        <ChatMessage key={idx} {...m} />
      ))}
    </div>
  );
}
