// VerticalResizer.tsx
import React, { useRef, useState } from "react";

export function VerticalResizer({ onBegin, onDrag }: {
  onBegin: (clientX: number) => void;
  onDrag: (clientX: number) => void;
}) {
  const dragging = useRef(false);
  const [isHovered, setIsHovered] = useState(false);

  function down(e: React.PointerEvent) {
    dragging.current = true;
    onBegin(e.clientX);
    e.currentTarget.setPointerCapture(e.pointerId);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }

  function move(e: React.PointerEvent) {
    if (!dragging.current) return;
    onDrag(e.clientX);
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
      aria-orientation="vertical"
      aria-label="Resize chat panel - drag left or right"
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerLeave={up}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`h-full w-4 sm:w-6 cursor-col-resize transition-all touch-manipulation relative ${
        dragging.current || isHovered
          ? 'bg-[#0f62ff] opacity-100 shadow-lg'
          : 'bg-gray-200 hover:bg-gray-300 active:bg-[#0f62ff] opacity-70 hover:opacity-100'
      }`}
      style={{
        cursor: dragging.current ? 'col-resize' : 'col-resize',
        touchAction: 'none',
        minWidth: '16px',
      }}
      title="Drag to resize chat panel"
    >
      {/* Visual indicator dots - always visible */}
      <div className={`h-full flex items-center justify-center transition-opacity ${
        dragging.current || isHovered ? 'opacity-100' : 'opacity-80'
      }`}>
        <div className="flex flex-col gap-1.5">
          <div className={`w-1.5 h-1.5 rounded-full ${dragging.current || isHovered ? 'bg-white' : 'bg-gray-600'}`}></div>
          <div className={`w-1.5 h-1.5 rounded-full ${dragging.current || isHovered ? 'bg-white' : 'bg-gray-600'}`}></div>
          <div className={`w-1.5 h-1.5 rounded-full ${dragging.current || isHovered ? 'bg-white' : 'bg-gray-600'}`}></div>
        </div>
      </div>
      {/* Extended invisible hit area for easier grabbing - extends beyond visible area */}
      <div 
        className="absolute inset-0 -left-4 -right-4 z-10" 
        style={{ touchAction: 'none', cursor: 'col-resize' }}
        aria-hidden="true"
      />
    </div>
  );
}
