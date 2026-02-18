import type { ChatApiResponse } from '../types';
import humps from 'humps';

export type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
};

// Use relative URL so it works through Vite proxy (for ngrok) or direct backend connection
const getChatApiUrl = (): string => {
  const runtimeEnv = (import.meta as any).env;
  // If VITE_API_BASE_URL is set and not localhost, use it (for production)
  const apiBase = runtimeEnv?.VITE_API_BASE_URL;
  if (apiBase && !apiBase.includes('localhost') && !apiBase.includes('127.0.0.1')) {
    return `${apiBase}/chat`;
  }
  // Otherwise use relative URL (works with Vite proxy for ngrok)
  return '/chat';
};

const DEFAULT_TIMEOUT = 60_000;

export interface ChatApiRequest {
  query: string;
}

export async function callChatApi(query: string): Promise<ChatApiResponse> {
  const apiUrl = getChatApiUrl();
  const timeout = DEFAULT_TIMEOUT;

  const payload: ChatApiRequest = {
    query
  };

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(id);

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status} - ${text}`);
    }

    const result = await res.json();
    const response = humps.camelizeKeys(result) as ChatApiResponse;
    return response;
  } catch (err: any) {
    if (err.name === 'AbortError') {
      throw new Error('Request timed out');
    }

    if (err?.message?.includes('Failed to fetch')) {
      throw new Error(`Cannot connect to backend. Is it running at ${apiUrl}?`);
    }

    throw new Error(err?.message ?? String(err));
  }
}
