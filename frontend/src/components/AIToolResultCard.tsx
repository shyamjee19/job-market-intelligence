import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";
import { Card } from "./ui/Card";
import { Skeleton } from "./ui/Skeleton";

interface AIToolResultCardProps {
  loading: boolean;
  error: string | null;
  summary: string | null;
  children?: ReactNode;
}

export function AIToolResultCard({ loading, error, summary, children }: AIToolResultCardProps) {
  if (loading) {
    return (
      <Card className="p-6">
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-5/6 mb-2" />
        <Skeleton className="h-4 w-3/4" />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="flex items-center gap-2 p-4" style={{ color: "var(--status-critical)" }}>
        <AlertTriangle size={16} />
        <span className="text-sm">{error}</span>
      </Card>
    );
  }

  if (!summary) return null;

  return (
    <Card className="p-6">
      <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: "var(--text-primary)" }}>
        {summary}
      </p>
      {children}
    </Card>
  );
}
