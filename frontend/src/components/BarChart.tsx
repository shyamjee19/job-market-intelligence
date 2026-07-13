import { useState } from "react";
import { Tooltip } from "./Tooltip";

interface BarChartProps {
  data: { label: string; count: number }[];
  color: string;
  title: string;
}

const ROW_HEIGHT = 32;
const BAR_THICKNESS = 16;

export function BarChart({ data, color, title }: BarChartProps) {
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
      <div>
        {data.map((d, index) => {
          const widthPct = max > 0 ? (d.count / max) * 100 : 0;
          return (
            <div
              key={d.label}
              className="flex items-center gap-3 rounded"
              style={{ height: ROW_HEIGHT }}
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const parent = e.currentTarget.parentElement!.getBoundingClientRect();
                setHovered({ index, x: rect.left - parent.left + 8, y: rect.top - parent.top });
              }}
              onMouseLeave={() => setHovered(null)}
            >
              <div
                className="text-sm truncate text-right"
                style={{ width: 140, color: "var(--text-secondary)" }}
                title={d.label}
              >
                {d.label}
              </div>
              <div className="flex-1 flex items-center">
                <div
                  className="rounded-full"
                  style={{
                    height: BAR_THICKNESS,
                    width: `${widthPct}%`,
                    minWidth: 4,
                    background: color,
                  }}
                />
                <span className="ml-2 text-sm tabular" style={{ color: "var(--text-primary)" }}>
                  {d.count}
                </span>
              </div>
            </div>
          );
        })}
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
