type ChatHeaderProps = {
  onClear: () => void;
  onToggleCollapse?: () => void;
};

export function ChatHeader({ onClear, onToggleCollapse }: ChatHeaderProps) {
  return (
    <div className="px-2 sm:px-3 py-2 sm:py-3 border-b border-[#eef4f8] flex items-center justify-between bg-white">
      <div className="flex items-center gap-2 flex-1 min-w-0">
        {/* Drag handle indicator */}
        <div className="flex flex-col gap-0.5 cursor-move touch-manipulation" title="Drag to resize">
          <div className="w-1 h-1 rounded-full bg-gray-400"></div>
          <div className="w-1 h-1 rounded-full bg-gray-400"></div>
          <div className="w-1 h-1 rounded-full bg-gray-400"></div>
        </div>
        <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-[#e9f7ff] flex items-center justify-center text-xs sm:text-sm font-semibold text-[#0b5aa6] shrink-0">
          C
        </div>
        <div className="font-semibold text-sm sm:text-base truncate">Sensa Sensor Chat</div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            className="p-1.5 sm:p-1 rounded hover:bg-gray-100 active:bg-gray-200 touch-manipulation transition-colors"
            aria-label="Collapse chat"
            title="Collapse chat"
          >
            <svg
              className="w-5 h-5 sm:w-4 sm:h-4 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
        <button
          onClick={onClear}
          className="text-xs sm:text-xs px-3 py-2 sm:px-2 sm:py-1 bg-red-50 text-red-700 rounded hover:bg-red-100 active:bg-red-200 touch-manipulation min-h-[44px] sm:min-h-0 transition-colors"
        >
          Clear chat
        </button>
      </div>
    </div>
  );
}
