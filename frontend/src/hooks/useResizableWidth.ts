// useChatWidth.ts
import { useState, useRef } from "react";
import type { ResizableWidthController } from "../types";

export function useResizableWidth(initial: number, min: number, max: number): ResizableWidthController {
  const [width, setWidth] = useState(initial);
  const startX = useRef(0);
  const startWidth = useRef(initial);

  function beginResize(clientX: number) {
    startX.current = clientX;
    startWidth.current = width;
  }

  function resizeTo(clientX: number) {
    const delta = clientX - startX.current;
    const next = Math.max(min, Math.min(max, startWidth.current - delta));
    setWidth(next);
  }

  return { width, beginResize, resizeTo };
}
