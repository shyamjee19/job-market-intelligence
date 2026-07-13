interface TooltipProps {
  x: number;
  y: number;
  title: string;
  value: string;
}

export function Tooltip({ x, y, title, value }: TooltipProps) {
  return (
    <div
      className="pointer-events-none absolute z-10 rounded-md px-2.5 py-1.5 text-sm shadow-lg"
      style={{
        left: x,
        top: y,
        transform: "translate(-50%, -110%)",
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        color: "var(--text-primary)",
        whiteSpace: "nowrap",
      }}
    >
      <div style={{ color: "var(--text-secondary)" }}>{title}</div>
      <div className="tabular font-semibold">{value}</div>
    </div>
  );
}
