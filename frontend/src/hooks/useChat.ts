import { useState, useRef, useEffect } from 'react';
import { callChatApi } from '../chat/chatService';
import type {
  ChatApiResponse,
  GraphData,
  GraphResultNode,
  GraphResultRel,
} from '../types';

export type ChatMessageType = {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
  timestamp: number;
};

function replaceAssistantPlaceholder(
  messages: ChatMessageType[],
  content: string
): ChatMessageType[] {
  const idx = [...messages]
    .reverse()
    .findIndex((m) => m.role === 'assistant' && m.loading);

  if (idx === -1)
    return [...messages, { role: 'assistant', content, timestamp: Date.now() }];

  const actualIdx = messages.length - 1 - idx;
  const assistantMsg: ChatMessageType = {
    role: 'assistant',
    content,
    timestamp: Date.now(),
  };
  const newList = [...messages];
  newList[actualIdx] = assistantMsg;
  return newList;
}

export function useChat() {
  const STORAGE_KEY = 'graph-rag-chat-messages';

  const [messages, setMessages] = useState<ChatMessageType[]>(() => {
    try {
      const storedMessages = localStorage.getItem(STORAGE_KEY);
      if (!storedMessages) return [];
      const parsed = JSON.parse(storedMessages) as ChatMessageType[];
      return parsed.filter((message) => !message.loading);
    } catch (err) {
      console.error('Failed to load messages from localStorage', err);
      return [];
    }
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesRef.current?.scrollTo({
      top: messagesRef.current.scrollHeight,
    });
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (err) {
      console.error('Failed to save messages to localStorage', err);
    }
  }, [messages]);

  async function sendMessage() {
    const text = input.trim();
    if (!text) return;

    setMessages((m) => [
      ...m,
      { role: 'user', content: text, timestamp: Date.now() },
      { role: 'assistant', content: '', loading: true, timestamp: Date.now() },
    ]);

    setInput('');
    setIsLoading(true);

    try {
      const response: ChatApiResponse = await callChatApi(text);

      setMessages((prev) =>
        replaceAssistantPlaceholder(prev, response.response)
      );
      
      // Graph visualization disabled for now - only showing answer text
      // if (response.entityRelationships?.entities && response.entityRelationships?.relationships) {
      //   updateGraph(
      //     response.entityRelationships.entities,
      //     response.entityRelationships.relationships
      //   );
      // }
    } catch (err: any) {
      setMessages((prev) =>
        replaceAssistantPlaceholder(
          prev,
          `Error: ${err.message || 'Failed to get response'}`
        )
      );
    } finally {
      setIsLoading(false);
    }
  }

  function clearMessages() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (err) {
      console.error('Failed to clear messages from localStorage', err);
    }
    setMessages([]);
  }

  function handleEnter(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function updateGraph(
    nodes: GraphResultNode[],
    relationships: GraphResultRel[]
  ) {
    setGraphData({ nodes, relationships });
  }

  return {
    messages,
    input,
    isLoading,
    messagesRef,
    setInput,
    sendMessage,
    handleEnter,
    graphData,
    clearMessages,
  };
}
