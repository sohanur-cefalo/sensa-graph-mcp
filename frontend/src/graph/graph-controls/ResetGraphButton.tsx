import React, { useState } from 'react';

interface Props {
  onClick: () => Promise<void>;
}

export default function ResetGraphButton({ onClick }: Props) {
  const [isResetting, setIsResetting] = useState(false);

  const handleClick = async () => {
    setIsResetting(true);
    try {
      await onClick();
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={isResetting}
      aria-label="Reset graph"
      className="inline-flex items-center gap-2 border border-gray-200 rounded-md px-2 py-1 bg-white hover:shadow-sm transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <svg
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="mr-1.5"
      >
        <path
          d="M21 12.79A9 9 0 1 1 11.21 3"
          stroke="#222"
          strokeWidth="1.4"
          fill="none"
        />
        <path d="M21 3v6h-6" stroke="#222" strokeWidth="1.4" fill="none" />
      </svg>
      {isResetting ? 'Resetting...' : 'Reset graph'}
    </button>
  );
}
