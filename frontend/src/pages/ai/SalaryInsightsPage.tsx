import { DollarSign } from "lucide-react";
import { useState } from "react";
import { getSalaryInsights } from "../../api/aiToolsClient";
import { AIToolResultCard } from "../../components/AIToolResultCard";
import { PageTransition } from "../../components/PageTransition";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { formatSalary } from "../../lib/format";
import type { AIToolResponse } from "../../types";

const inputStyle = { background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" };

export function SalaryInsightsPage() {
  const [role, setRole] = useState("");
  const [location, setLocation] = useState("");
  const [result, setResult] = useState<AIToolResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await getSalaryInsights(role || undefined, location || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compute salary insights");
    } finally {
      setLoading(false);
    }
  }

  const data = result?.data as
    | { sample_size: number; avg_salary_min: number | null; avg_salary_max: number | null; highest_salary: number | null }
    | undefined;

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          <DollarSign size={22} style={{ color: "var(--series-violet)" }} />
          AI Salary Insights
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Real salary statistics computed from current postings, with an AI narrative on top.
        </p>

        <Card className="p-5 mb-4 flex flex-col gap-3">
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="Role (optional, e.g. Backend Engineer)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Location (optional)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <Button variant="primary" disabled={loading} onClick={handleSubmit} className="self-start">
            {loading ? "Computing…" : "Get insights"}
          </Button>
        </Card>

        {data && (
          <div className="grid grid-cols-3 gap-3 mb-4">
            <Card className="p-4">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Avg. range
              </p>
              <p className="text-lg font-semibold tabular mt-1" style={{ color: "var(--text-primary)" }}>
                {formatSalary(data.avg_salary_min, data.avg_salary_max)}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Highest observed
              </p>
              <p className="text-lg font-semibold tabular mt-1" style={{ color: "var(--text-primary)" }}>
                {data.highest_salary ? `$${data.highest_salary.toLocaleString()}` : "—"}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Sample size
              </p>
              <p className="text-lg font-semibold tabular mt-1" style={{ color: "var(--text-primary)" }}>
                {data.sample_size}
              </p>
            </Card>
          </div>
        )}

        <AIToolResultCard loading={loading} error={error} summary={result?.summary ?? null} />
      </div>
    </PageTransition>
  );
}
