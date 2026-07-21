export function formatSalary(min: number | null, max: number | null): string {
  if (!min && !max) return "Not disclosed";
  const fmt = (n: number) => `$${Math.round(n / 1000)}k`;
  if (min && max && min !== max) return `${fmt(min)} – ${fmt(max)}`;
  return fmt((min ?? max) as number);
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

const SOURCE_LABELS: Record<string, string> = {
  remoteok: "RemoteOK",
  arbeitnow: "Arbeitnow",
};

const SOURCE_COLOR_VARS: Record<string, string> = {
  remoteok: "--series-blue",
  arbeitnow: "--series-aqua",
};

export function formatSource(source: string): string {
  return SOURCE_LABELS[source] ?? source.charAt(0).toUpperCase() + source.slice(1);
}

export function sourceColorVar(source: string): string {
  return SOURCE_COLOR_VARS[source] ?? "--series-violet";
}
