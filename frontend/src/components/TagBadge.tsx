import type { MouseEvent } from "react";

interface TagBadgeProps {
  tag: string;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
}

export function TagBadge({ tag, onClick }: TagBadgeProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-full px-2.5 py-0.5 text-xs transition-colors duration-150"
      style={{
        background: "var(--surface-2)",
        border: "1px solid var(--border)",
        color: "var(--text-secondary)",
        cursor: onClick ? "pointer" : "default",
      }}
    >
      {tag}
    </button>
  );
}
