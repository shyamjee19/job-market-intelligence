import { FileText } from "lucide-react";
import { useState } from "react";
import { analyzeResume } from "../../api/aiToolsClient";
import { AIToolResultCard } from "../../components/AIToolResultCard";
import { PageTransition } from "../../components/PageTransition";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import type { AIToolResponse } from "../../types";

export function ResumeAnalyzerPage() {
  const [resumeText, setResumeText] = useState("");
  const [result, setResult] = useState<AIToolResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await analyzeResume(resumeText));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze resume");
    } finally {
      setLoading(false);
    }
  }

  const topSkills = (result?.data?.top_market_skills as string[] | undefined) ?? [];

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          <FileText size={22} style={{ color: "var(--series-violet)" }} />
          AI Resume Analyzer
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Paste your resume text for structured feedback, checked against skills actually in demand right now.
        </p>

        <Card className="p-5 mb-4">
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste your resume text here (at least 50 characters)…"
            rows={10}
            className="w-full rounded-lg text-sm px-3.5 py-2.5 outline-none resize-y"
            style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
          />
          <Button
            variant="primary"
            className="mt-3"
            disabled={loading || resumeText.trim().length < 50}
            onClick={handleSubmit}
          >
            {loading ? "Analyzing…" : "Analyze resume"}
          </Button>
        </Card>

        <AIToolResultCard loading={loading} error={error} summary={result?.summary ?? null}>
          {topSkills.length > 0 && (
            <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border)" }}>
              <p className="text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Currently in-demand skills
              </p>
              <div className="flex flex-wrap gap-1.5">
                {topSkills.map((s) => (
                  <span
                    key={s}
                    className="text-xs rounded-full px-2.5 py-1"
                    style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </AIToolResultCard>
      </div>
    </PageTransition>
  );
}
