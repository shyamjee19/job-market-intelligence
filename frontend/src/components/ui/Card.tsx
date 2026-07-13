import type { HTMLAttributes } from "react";
import clsx from "clsx";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hoverable?: boolean;
}

export function Card({ hoverable, className, style, children, ...rest }: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-xl transition-shadow duration-200",
        hoverable && "hover:shadow-[var(--shadow-md)]",
        className,
      )}
      style={{
        background: "var(--surface-1)",
        border: "1px solid var(--border)",
        boxShadow: "var(--shadow-sm)",
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  );
}
