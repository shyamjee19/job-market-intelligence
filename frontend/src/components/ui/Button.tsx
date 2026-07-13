import type { ButtonHTMLAttributes } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
}

export function Button({ variant = "secondary", size = "md", className, style, ...rest }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-lg font-medium transition-all duration-150 active:scale-[0.97] disabled:opacity-40 disabled:pointer-events-none";
  const sizing = size === "sm" ? "px-2.5 py-1.5 text-xs" : "px-3.5 py-2 text-sm";

  const variantStyle: React.CSSProperties =
    variant === "primary"
      ? { background: "var(--series-blue)", color: "#fff" }
      : variant === "ghost"
        ? { background: "transparent", color: "var(--text-secondary)" }
        : { background: "var(--surface-1)", color: "var(--text-primary)", border: "1px solid var(--border)" };

  return (
    <button
      className={clsx(base, sizing, variant !== "ghost" && "hover:brightness-95", className)}
      style={{ ...variantStyle, ...style }}
      {...rest}
    />
  );
}
