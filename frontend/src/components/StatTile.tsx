import type { LucideIcon } from "lucide-react";
import { Card } from "./ui/Card";

interface StatTileProps {
  label: string;
  value: string;
  icon: LucideIcon;
  colorVar: string;
}

export function StatTile({ label, value, icon: Icon, colorVar }: StatTileProps) {
  return (
    <Card hoverable className="flex-1 min-w-[160px] p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm" style={{ color: "var(--text-secondary)" }}>
          {label}
        </span>
        <div
          className="flex items-center justify-center rounded-lg w-7 h-7"
          style={{ background: `color-mix(in srgb, var(${colorVar}) 14%, transparent)`, color: `var(${colorVar})` }}
        >
          <Icon size={15} />
        </div>
      </div>
      <div className="text-3xl font-semibold mt-2 tabular" style={{ color: "var(--text-primary)" }}>
        {value}
      </div>
    </Card>
  );
}
