import { Compass } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { getCareerAdvice } from "../../api/aiToolsClient";
import { AIToolResultCard } from "../../components/AIToolResultCard";
import { PageTransition } from "../../components/PageTransition";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import type { AIToolResponse } from "../../types";

const inputStyle = { background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" };

interface SampleJob {
  id: number;
  position: string | null;
  company: string | null;
  location: string | null;
}

export function CareerAdvisorPage() {
  const [currentSkills, setCurrentSkills] = useState("");
  const [goal, setGoal] = useState("");
  const [result, setResult] = useState<AIToolResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await getCareerAdvice(currentSkills, goal));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate career advice");
    } finally {
      setLoading(false);
    }
  }

  const sampleJobs = (result?.data?.sample_jobs as SampleJob[] | undefined) ?? [];

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          <Compass size={22} style={{ color: "var(--series-violet)" }} />
          AI Career Advisor
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Get a concrete roadmap toward your next role, grounded in postings that actually match your goal.
        </p>

        <Card className="p-5 mb-4 flex flex-col gap-3">
          <input
            value={currentSkills}
            onChange={(e) => setCurrentSkills(e.target.value)}
            placeholder="Your current skills (e.g. Python, SQL, Docker)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <input
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Your goal (e.g. Senior Backend Engineer)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <Button variant="primary" disabled={loading || !currentSkills.trim() || !goal.trim()} onClick={handleSubmit} className="self-start">
            {loading ? "Thinking…" : "Get advice"}
          </Button>
        </Card>

        <AIToolResultCard loading={loading} error={error} summary={result?.summary ?? null}>
          {sampleJobs.length > 0 && (
            <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border)" }}>
              <p className="text-xs font-medium mb-2" style={{ color: "var(--text-secondary)" }}>
                Real postings this advice was grounded in
              </p>
              <div className="flex flex-col gap-1.5">
                {sampleJobs.map((j) => (
                  <Link
                    key={j.id}
                    to={`/jobs/${j.id}`}
                    className="text-sm hover:underline"
                    style={{ color: "var(--series-blue)" }}
                  >
                    {j.position} · {j.company}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </AIToolResultCard>
      </div>
    </PageTransition>
  );
}
