import clsx from "clsx";

export function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <div className={clsx("skeleton", className)} style={style} />;
}

export function SkeletonTableRows({ rows = 8 }: { rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
          <td className="px-4 py-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full shrink-0" />
              <Skeleton className="h-4 w-40" />
            </div>
          </td>
          <td className="px-4 py-3">
            <Skeleton className="h-4 w-28" />
          </td>
          <td className="px-4 py-3">
            <Skeleton className="h-4 w-24" />
          </td>
          <td className="px-4 py-3">
            <Skeleton className="h-4 w-20" />
          </td>
          <td className="px-4 py-3">
            <Skeleton className="h-5 w-32 rounded-full" />
          </td>
          <td className="px-4 py-3">
            <Skeleton className="h-4 w-20" />
          </td>
        </tr>
      ))}
    </>
  );
}

export function SkeletonStatTile() {
  return (
    <div
      className="flex-1 min-w-[160px] rounded-xl p-4"
      style={{ background: "var(--surface-1)", border: "1px solid var(--border)" }}
    >
      <Skeleton className="h-3.5 w-24 mb-3" />
      <Skeleton className="h-8 w-16" />
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div>
      <Skeleton className="h-3.5 w-40 mb-4" />
      <div className="flex items-end gap-3" style={{ height: 180 }}>
        {[60, 90, 45, 120, 75, 100, 50].map((h, i) => (
          <Skeleton key={i} className="flex-1 rounded-t-md" style={{ height: h }} />
        ))}
      </div>
    </div>
  );
}
