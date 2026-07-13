import { useRef, useState } from "react";
import { COUNTRY_PATHS, MAP_HEIGHT, MAP_WIDTH, backendNameToMapName } from "../lib/worldMap";
import { Tooltip } from "./Tooltip";

interface WorldMapProps {
  data: { label: string; count: number }[];
  totalJobs: number;
}

// Sequential blue ramp, light -> dark (palette.md steps 100/300/450/600/700).
// A discrete/ordinal scale reads more clearly at this size than a
// continuous gradient, and stays legible if hues ever get printed in gray.
const BUCKET_COLORS = ["#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"];

function bucketColor(count: number, max: number): string {
  if (count <= 0 || max <= 0) return "var(--surface-2)";
  const ratio = count / max;
  const index = Math.min(BUCKET_COLORS.length - 1, Math.floor(ratio * BUCKET_COLORS.length));
  return BUCKET_COLORS[index];
}

export function WorldMap({ data, totalJobs }: WorldMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<{ name: string; count: number; x: number; y: number } | null>(null);

  const countsByMapName = new Map(data.map((d) => [backendNameToMapName(d.label), d.count]));
  const max = Math.max(...data.map((d) => d.count), 1);
  const totalMapped = data.reduce((sum, d) => sum + d.count, 0);

  function handleHover(name: string, count: number, e: React.MouseEvent<SVGPathElement>) {
    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;
    const rect = e.currentTarget.getBoundingClientRect();
    setHovered({
      name,
      count,
      x: rect.left - containerRect.left + rect.width / 2,
      y: rect.top - containerRect.top + rect.height / 2,
    });
  }

  return (
    <div className="relative" ref={containerRef}>
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
          World hiring map
        </h3>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          {totalMapped.toLocaleString()} of {totalJobs.toLocaleString()} postings mapped (best-effort location matching)
        </span>
      </div>

      <svg viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} className="w-full" style={{ height: MAP_HEIGHT * 0.6 }}>
        {COUNTRY_PATHS.map((country) => {
          const count = countsByMapName.get(country.name) ?? 0;
          return (
            <path
              key={country.name}
              d={country.d}
              fill={bucketColor(count, max)}
              stroke="var(--page-plane)"
              strokeWidth={0.5}
              onMouseEnter={(e) => handleHover(country.name, count, e)}
              onMouseLeave={() => setHovered(null)}
              style={{ cursor: count > 0 ? "pointer" : "default" }}
            />
          );
        })}
      </svg>

      <div className="flex items-center gap-1.5 mt-2">
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          Fewer
        </span>
        {BUCKET_COLORS.map((color) => (
          <span key={color} className="h-2.5 w-6 rounded-sm" style={{ background: color }} />
        ))}
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          More
        </span>
      </div>

      {hovered && (
        <Tooltip x={hovered.x} y={hovered.y} title={hovered.name} value={`${hovered.count} postings`} />
      )}
    </div>
  );
}
