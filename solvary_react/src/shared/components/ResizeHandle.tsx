import { useRef, type PointerEvent } from 'react';

interface Props {
  /** `col` = a vertical bar you drag left/right; `row` = a horizontal bar you drag up/down. */
  direction: 'col' | 'row';
  /** Called with the pointer delta (px) since the previous move event. */
  onDrag: (delta: number) => void;
  onDoubleClick?: () => void;
  className?: string;
}

/**
 * A thin draggable splitter. Pointer capture keeps the drag alive when the
 * cursor outruns the bar; text selection and the cursor are pinned on the
 * body for the duration so Monaco/markdown don't fight the drag.
 */
export function ResizeHandle({ direction, onDrag, onDoubleClick, className = '' }: Props) {
  const lastRef = useRef<number | null>(null);
  const isCol = direction === 'col';

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    lastRef.current = isCol ? e.clientX : e.clientY;
    document.body.style.cursor = isCol ? 'col-resize' : 'row-resize';
    document.body.style.userSelect = 'none';
  };
  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    if (lastRef.current === null) return;
    const pos = isCol ? e.clientX : e.clientY;
    onDrag(pos - lastRef.current);
    lastRef.current = pos;
  };
  const onPointerUp = (e: PointerEvent<HTMLDivElement>) => {
    if (lastRef.current === null) return;
    lastRef.current = null;
    e.currentTarget.releasePointerCapture(e.pointerId);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  };

  return (
    <div
      role="separator"
      aria-orientation={isCol ? 'vertical' : 'horizontal'}
      title="Drag to resize · double-click to reset"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onDoubleClick={onDoubleClick}
      className={`group shrink-0 relative z-10 ${
        isCol ? 'w-1.5 cursor-col-resize' : 'h-1.5 cursor-row-resize'
      } bg-gray-200 hover:bg-indigo-400 active:bg-indigo-500 transition-colors ${className}`}
    >
      {/* wider invisible hit area */}
      <div className={`absolute ${isCol ? '-left-1 -right-1 inset-y-0' : '-top-1 -bottom-1 inset-x-0'}`} />
    </div>
  );
}
