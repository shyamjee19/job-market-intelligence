import { CheckCircle2, MessageSquareText } from "lucide-react";
import { useState } from "react";
import { getInterviewPrep } from "../../api/aiToolsClient";
import { AIToolResultCard } from "../../components/AIToolResultCard";
import { PageTransition } from "../../components/PageTransition";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import type { AIToolResponse } from "../../types";

const inputStyle = { background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" };

export function InterviewPrepPage() {
  const [role, setRole] = useState("");
  const [company, setCompany] = useState("");
  const [result, setResult] = useState<AIToolResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await getInterviewPrep(role, company || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to prepare interview questions");
    } finally {
      setLoading(false);
    }
  }

  const grounded = result?.data?.grounded_in_real_postings as boolean | undefined;

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          <MessageSquareText size={22} style={{ color: "var(--series-violet)" }} />
          AI Interview Preparation
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Likely interview questions and prep tips for a target role — grounded in real postings when a company is given.
        </p>

        <Card className="p-5 mb-4 flex flex-col gap-3">
          <input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="Target role (e.g. Frontend Engineer)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Company (optional)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <Button variant="primary" disabled={loading || !role.trim()} onClick={handleSubmit} className="self-start">
            {loading ? "Preparing…" : "Prepare me"}
          </Button>
        </Card>

        <AIToolResultCard loading={loading} error={error} summary={result?.summary ?? null}>
          {grounded !== undefined && (
            <div className="mt-3 pt-3 flex items-center gap-1.5 text-xs" style={{ borderTop: "1px solid var(--border)", color: "var(--text-muted)" }}>
              <CheckCircle2 size={13} style={{ color: grounded ? "var(--status-good)" : "var(--text-muted)" }} />
              {grounded ? "Grounded in real postings for this company" : "No real postings found for this company — generic answer"}
            </div>
          )}
        </AIToolResultCard>
      </div>
    </PageTransition>
  );
}
