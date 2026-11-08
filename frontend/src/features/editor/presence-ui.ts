export function presenceColor(userId: string): string {
  const palette = ['#35d0ba', '#a78bfa', '#60a5fa', '#fbbf24', '#fb7185', '#a3e635']
  const hash = [...userId].reduce((sum, char) => (sum * 31 + char.charCodeAt(0)) >>> 0, 0)
  return palette[hash % palette.length]!
}

export function cursorOnCanvas(
  cursor: { x: number; y: number }, viewport: { x: number; y: number; zoom: number },
): { left: string; top: string } {
  return { left: `${cursor.x * viewport.zoom + viewport.x}px`, top: `${cursor.y * viewport.zoom + viewport.y}px` }
}
