import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatTimestamp } from '../utils/formatTimestamp';
export type ChatMessageProps = {
  role: 'user' | 'assistant';
  content: string;
  loading?: boolean;
  timestamp: number;
};

export function Spinner() {
  return (
    <div className="flex items-center gap-2">
      <svg className="w-4 h-4 text-[#0f1723] animate-spin" viewBox="0 0 24 24">
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
          fill="none"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        />
      </svg>
      <div className="text-sm opacity-90">Thinking…</div>
    </div>
  );
}

export function ChatMessage({
  role,
  content,
  loading,
  timestamp,
}: ChatMessageProps) {
  const isUser = role === 'user';
  
  // Debug: Log content length to verify full content is received
  if (process.env.NODE_ENV === 'development' && content) {
    console.log(`ChatMessage ${role} content length:`, content.length, 'chars');
  }
  
  return (
    <div
      className={`flex items-start gap-2 py-2 ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      {!isUser && (
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#e6eef6] flex items-center justify-center text-xs sm:text-sm font-semibold text-[#1f3761] shrink-0">
          A
        </div>
      )}
      <div className={`flex flex-col max-w-[90%] sm:max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Bubble */}
        <div
          className={`message-markdown w-full px-3 py-2 rounded-lg leading-relaxed text-base sm:text-sm break-words
          ${
            isUser
              ? 'bg-[#1f6feb] text-white rounded-tr-sm rounded-br-sm'
              : 'bg-[#f3f7fb] text-[#0f1723] rounded-tl-sm rounded-bl-sm'
          }
          **:m-0
          [&_p]:mb-1 [&_p]:break-words [&_p]:whitespace-normal [&_p]:overflow-visible
          [&_h2]:mb-1 [&_h2]:font-semibold [&_h2]:text-lg sm:[&_h2]:text-base [&_h2]:break-words
          [&_h3]:mb-1 [&_h3]:font-semibold [&_h3]:text-base sm:[&_h3]:text-sm [&_h3]:break-words
          [&_ul]:ml-4 [&_ul]:mb-1
          [&_li]:mb-0.5 [&_li]:break-words
          [&_td]:break-words [&_th]:break-words
        `}
        style={{ minHeight: 'auto', maxHeight: 'none' }}
        >
          {loading ? (
            <Spinner />
          ) : (
            <div className="markdown-wrapper w-full" style={{ whiteSpace: 'normal', wordWrap: 'break-word' }}>
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ node, ...props }) => (
                    <div className="overflow-x-auto my-2">
                      <table className="min-w-full border-collapse border border-gray-300" {...props} />
                    </div>
                  ),
                  thead: ({ node, ...props }) => (
                    <thead className="bg-gray-100" {...props} />
                  ),
                  tbody: ({ node, ...props }) => (
                    <tbody {...props} />
                  ),
                  tr: ({ node, ...props }) => (
                    <tr className="border-b border-gray-200" {...props} />
                  ),
                  th: ({ node, ...props }) => (
                    <th className="border border-gray-300 px-3 py-2 text-left font-semibold" {...props} />
                  ),
                  td: ({ node, ...props }) => (
                    <td className="border border-gray-300 px-3 py-2" {...props} />
                  ),
                  a: ({ node, ...props }) => (
                    <a
                      className="text-blue-600 hover:text-blue-800 underline"
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    />
                  ),
                  p: ({ node, ...props }) => (
                    <p className="mb-2" {...props} />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc ml-4 mb-2" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="list-decimal ml-4 mb-2" {...props} />
                  ),
                  li: ({ node, ...props }) => (
                    <li className="mb-1" {...props} />
                  ),
                  code: ({ node, inline, ...props }: any) =>
                    inline ? (
                      <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props} />
                    ) : (
                      <code className="block bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto" {...props} />
                    ),
                  pre: ({ node, ...props }) => (
                    <pre className="bg-gray-100 p-2 rounded text-sm font-mono overflow-x-auto mb-2" {...props} />
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        <div className="text-xs sm:text-xs mt-1 text-[#6b7280]">
          {formatTimestamp(timestamp)}
        </div>
      </div>
      {isUser && (
        <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#c7e0ff] flex items-center justify-center text-xs sm:text-sm font-semibold text-[#05305b] shrink-0">
          U
        </div>
      )}
    </div>
  );
}
