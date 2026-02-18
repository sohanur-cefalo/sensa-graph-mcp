// HorizontalResizer.tsx - For resizing height (used on mobile)
import React, { useRef, useState } from "react";

export function HorizontalResizer({ onBegin, onDrag }: {
  onBegin: (clientY: number) => void;
  onDrag: (clientY: number) => void;
}) {
  const dragging = useRef(false);
  const [isHovered, setIsHovered] = useState(false);

  function down(e: React.PointerEvent) {
    dragging.current = true;
    onBegin(e.clientY);
    e.currentTarget.setPointerCapture(e.pointerId);
    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';
  }

  function move(e: React.PointerEvent) {
    if (!dragging.current) return;
    onDrag(e.clientY);
  }

  function up(e: React.PointerEvent) {
    dragging.current = false;
    e.currentTarget.releasePointerCapture(e.pointerId);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }

  return (
    <div
      role="separator"
      aria-orientation="horizontal"
      aria-label="Resize chat panel height"
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerLeave={up}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`h-2 cursor-row-resize transition-colors touch-manipulation relative ${
        dragging.current || isHovered
          ? 'bg-[#0f62ff]'
          : 'bg-transparent hover:bg-gray-300 active:bg-[#0f62ff]'
      }`}
      style={{
        cursor: dragging.current ? 'row-resize' : 'row-resize',
        touchAction: 'none',
      }}
    >
      {/* Visual indicator dots */}
      <div className={`h-full flex items-center justify-center transition-opacity ${
        dragging.current || isHovered ? 'opacity-100' : 'opacity-50 md:opacity-0 md:hover:opacity-100'
      }`}>
        <div className="flex gap-1">
          <div className={`w-1 h-1 rounded-full ${dragging.current || isHovered ? 'bg-white' : 'bg-gray-400'}`}></div>
          <div className={`w-1 h-1 rounded-full ${dragging.current || isHovered ? 'bg-white' : 'bg-gray-400'}`}></div>
          <div className={`w-1 h-1 rounded-full ${dragging.current || isHovered ? 'bg-white' : 'bg-gray-400'}`}></div>
        </div>
      </div>
    </div>
  );
}
