import React from 'react';

interface Props {
  onClick: () => void;
}

export default function LoadFromNeo4jButton({ onClick }: Props) {
  return (
    <button
      onClick={onClick}
      title="Load graph data from the backend API"
      aria-label="Load graph"
      className="inline-flex items-center gap-2 border border-gray-200 rounded-md px-3 py-2 sm:px-2 sm:py-1 bg-white hover:shadow-sm active:shadow-none transition-shadow touch-manipulation min-h-[44px] sm:min-h-0"
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="shrink-0"
      >
        <path
          d="M12 2C7.03 2 3 3.79 3 6v12c0 2.21 4.03 4 9 4s9-1.79 9-4V6c0-2.21-4.03-4-9-4z"
          stroke="#222"
          strokeWidth="1"
          fill="#fff"
        />
        <path
          d="M3 8c2.5 1.5 6.5 1.5 9 0 2.5-1.5 6.5-1.5 9 0"
          stroke="#222"
          strokeWidth="1"
          fill="none"
        />
      </svg>

      <span className="text-sm sm:text-sm">Load Graph</span>
      <span className="sr-only">Load graph</span>
    </button>
  );
}
