import { useRef, useState } from "react";
import { Tooltip } from "./Tooltip";

interface AreaChartProps {
  data: { date: string; count: number }[];
  color: string;
  title: string;
}

const WIDTH = 600;
const HEIGHT = 180;
const PAD = 8;

export function AreaChart({ data, color, title }: AreaChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState<{ index: number; x: number; y: number } | null>(null);

  if (data.length === 0) {
    return <p style={{ color: "var(--text-muted)" }}>No data yet.</p>;
  }

  const max = Math.max(...data.map((d) => d.count), 1);
  const stepX = data.length > 1 ? (WIDTH - PAD * 2) / (data.length - 1) : 0;

  const points = data.map((d, i) => ({
    x: PAD + i * stepX,
    y: PAD + (HEIGHT - PAD * 2) * (1 - d.count / max),
  }));

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${HEIGHT - PAD} L ${points[0].x} ${HEIGHT - PAD} Z`;

  function handleHover(index: number, e: React.MouseEvent<SVGRectElement>) {
    const containerRect = containerRef.current?.getBoundingClientRect();
    if (!containerRect) return;
    const svgRect = e.currentTarget.ownerSVGElement!.getBoundingClientRect();
    const scaleX = svgRect.width / WIDTH;
    const scaleY = svgRect.height / HEIGHT;
    setHovered({
      index,
      x: svgRect.left - containerRect.left + points[index].x * scaleX,
      y: svgRect.top - containerRect.top + points[index].y * scaleY,
    });
  }

  return (
    <div className="relative" ref={containerRef}>
      <h3 className="text-sm font-medium mb-3" style={{ color: "var(--text-secondary)" }}>
        {title}
      </h3>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="none" className="w-full" style={{ height: HEIGHT }}>
        <line
          x1={PAD}
          y1={HEIGHT - PAD}
          x2={WIDTH - PAD}
          y2={HEIGHT - PAD}
          stroke="var(--baseline)"
          strokeWidth={1}
        />
        <path d={areaPath} fill={color} opacity={0.1} stroke="none" />
        <path d={linePath} fill="none" stroke={color} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />

        {hovered !== null && (
          <>
            <line
              x1={points[hovered.index].x}
              y1={PAD}
              x2={points[hovered.index].x}
              y2={HEIGHT - PAD}
              stroke="var(--gridline)"
              strokeWidth={1}
            />
            <circle
              cx={points[hovered.index].x}
              cy={points[hovered.index].y}
              r={5}
              fill={color}
              stroke="var(--surface-1)"
              strokeWidth={2}
            />
          </>
        )}

        {points.map((p, i) => (
          <rect
            key={data[i].date}
            x={p.x - stepX / 2}
            y={0}
            width={stepX || WIDTH}
            height={HEIGHT}
            fill="transparent"
            onMouseEnter={(e) => handleHover(i, e)}
            onMouseLeave={() => setHovered(null)}
          />
        ))}
      </svg>
      {hovered !== null && (
        <Tooltip
          x={hovered.x}
          y={hovered.y}
          title={data[hovered.index].date}
          value={String(data[hovered.index].count)}
        />
      )}
    </div>
  );
}
