import { useState } from "react";
import { Tooltip } from "./Tooltip";

interface ColumnChartProps {
  data: { label: string; count: number }[];
  color: string;
  title: string;
}

const CHART_HEIGHT = 180;
const BAR_THICKNESS = 24;

export function ColumnChart({ data, color, title }: ColumnChartProps) {
  const [hovered, setHovered] = useState<{ index: number; x: number; y: number } | null>(null);

  if (data.length === 0) {
    return <p style={{ color: "var(--text-muted)" }}>No data yet.</p>;
  }

  const max = Math.max(...data.map((d) => d.count));

  return (
    <div className="relative">
      <h3 className="text-sm font-medium mb-3" style={{ color: "var(--text-secondary)" }}>
        {title}
      </h3>
      <div
        className="flex items-end gap-3 px-2"
        style={{ height: CHART_HEIGHT, borderBottom: "1px solid var(--baseline)" }}
      >
        {data.map((d, index) => {
          const heightPx = max > 0 ? Math.max((d.count / max) * (CHART_HEIGHT - 24), 2) : 2;
          return (
            <div key={d.label} className="flex flex-col items-center" style={{ width: BAR_THICKNESS + 12 }}>
              <span className="text-xs tabular mb-1" style={{ color: "var(--text-primary)" }}>
                {d.count}
              </span>
              <div
                className="rounded-t-[4px]"
                style={{ height: heightPx, width: BAR_THICKNESS, background: color }}
                onMouseEnter={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const parent = e.currentTarget.closest(".relative")!.getBoundingClientRect();
                  setHovered({ index, x: rect.left - parent.left + rect.width / 2, y: rect.top - parent.top });
                }}
                onMouseLeave={() => setHovered(null)}
              />
            </div>
          );
        })}
      </div>
      <div className="flex gap-3 px-2 mt-1">
        {data.map((d) => (
          <div
            key={d.label}
            className="text-xs text-center tabular"
            style={{ width: BAR_THICKNESS + 12, color: "var(--text-muted)" }}
          >
            {d.label}
          </div>
        ))}
      </div>
      {hovered && (
        <Tooltip
          x={hovered.x}
          y={hovered.y}
          title={data[hovered.index].label}
          value={String(data[hovered.index].count)}
        />
      )}
    </div>
  );
}
