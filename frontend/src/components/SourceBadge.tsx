import { formatSource, sourceColorVar } from "../lib/format";

export function SourceBadge({ source }: { source: string }) {
  const colorVar = sourceColorVar(source);
  return (
    <span
      className="rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap"
      style={{
        background: `color-mix(in srgb, var(${colorVar}) 14%, var(--surface-1))`,
        color: `var(${colorVar})`,
      }}
    >
      {formatSource(source)}
    </span>
  );
}
