import type { InputHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: ReactNode;
  onClear?: () => void;
}

export function Input({ icon, onClear, className, value, ...rest }: InputProps) {
  return (
    <div className={clsx("relative flex items-center", className)}>
      {icon && (
        <span className="absolute left-3 flex items-center pointer-events-none" style={{ color: "var(--text-muted)" }}>
          {icon}
        </span>
      )}
      <input
        value={value}
        className="w-full rounded-lg text-sm transition-colors duration-150 outline-none"
        style={{
          background: "var(--surface-1)",
          border: "1px solid var(--border)",
          color: "var(--text-primary)",
          padding: `8px 12px 8px ${icon ? "36px" : "12px"}`,
          paddingRight: onClear && value ? "32px" : undefined,
        }}
        {...rest}
      />
      {onClear && !!value && (
        <button
          type="button"
          onClick={onClear}
          className="absolute right-2.5 rounded-full p-0.5 hover:bg-black/5 dark:hover:bg-white/10"
          style={{ color: "var(--text-muted)" }}
          aria-label="Clear"
        >
          ×
        </button>
      )}
    </div>
  );
}
