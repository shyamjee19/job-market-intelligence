const SERIES_VARS = [
  "--series-blue",
  "--series-aqua",
  "--series-violet",
  "--series-orange",
  "--series-green",
  "--series-magenta",
  "--series-red",
  "--series-yellow",
];

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

interface AvatarProps {
  name: string;
  size?: number;
}

export function Avatar({ name, size = 32 }: AvatarProps) {
  const initial = (name?.trim()?.[0] ?? "?").toUpperCase();
  const colorVar = SERIES_VARS[hashString(name ?? "") % SERIES_VARS.length];

  return (
    <div
      className="flex items-center justify-center rounded-full font-semibold shrink-0"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.42,
        background: `color-mix(in srgb, var(${colorVar}) 18%, var(--surface-1))`,
        color: `var(${colorVar})`,
      }}
    >
      {initial}
    </div>
  );
}
