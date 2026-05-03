import React, { useEffect, useRef } from 'react';

interface VirtualChunkRowProps {
  style: React.CSSProperties;
  chunkIndex: number;
  contentHtml: string;
  isActive: boolean;
  registerRef: (el: HTMLDivElement | null, index: number) => void;
}

/**
 * Отдельная строка виртуализированного списка чанков.
 *
 * Принимает style от react-window (top, width, height) и
 * передаёт DOM-элемент родителю через registerRef для
 * последующего наблюдения через IntersectionObserver.
 */
export const VirtualChunkRow: React.FC<VirtualChunkRowProps> = ({
  style,
  chunkIndex,
  contentHtml,
  isActive,
  registerRef,
}) => {
  const internalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = internalRef.current;
    if (el) {
      registerRef(el, chunkIndex);
    }
    return () => {
      registerRef(null, chunkIndex);
    };
  }, [chunkIndex, registerRef]);

  return (
    <div
      ref={internalRef}
      className={`reader-chunk ${isActive ? 'reader-chunk--active' : ''}`}
      data-chunk-index={chunkIndex}
      style={{
        ...style,
        minHeight: style.height || '100px',
      }}
      dangerouslySetInnerHTML={{ __html: contentHtml }}
    />
  );
};
