import { Target } from "lucide-react";
import { useState } from "react";
import { getSkillGap } from "../../api/aiToolsClient";
import { AIToolResultCard } from "../../components/AIToolResultCard";
import { PageTransition } from "../../components/PageTransition";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import type { AIToolResponse } from "../../types";

const inputStyle = { background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" };

interface SkillDemand {
  skill: string;
  demand_count: number;
}

export function SkillGapPage() {
  const [currentSkills, setCurrentSkills] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [result, setResult] = useState<AIToolResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      setResult(await getSkillGap(currentSkills, targetRole));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze skill gap");
    } finally {
      setLoading(false);
    }
  }

  const have = (result?.data?.have as SkillDemand[] | undefined) ?? [];
  const missing = (result?.data?.missing as SkillDemand[] | undefined) ?? [];
  const sampleSize = result?.data?.sample_size as number | undefined;

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          <Target size={22} style={{ color: "var(--series-violet)" }} />
          AI Skill Gap Analysis
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          See exactly which in-demand skills you're missing for a target role, ranked by real posting counts.
        </p>

        <Card className="p-5 mb-4 flex flex-col gap-3">
          <input
            value={currentSkills}
            onChange={(e) => setCurrentSkills(e.target.value)}
            placeholder="Your current skills, comma separated"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <input
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="Target role (e.g. Data Engineer)"
            className="rounded-lg text-sm px-3.5 py-2.5 outline-none"
            style={inputStyle}
          />
          <Button variant="primary" disabled={loading || !currentSkills.trim() || !targetRole.trim()} onClick={handleSubmit} className="self-start">
            {loading ? "Analyzing…" : "Analyze gap"}
          </Button>
        </Card>

        <AIToolResultCard loading={loading} error={error} summary={result?.summary ?? null}>
          {(have.length > 0 || missing.length > 0) && (
            <div className="mt-4 pt-4 grid sm:grid-cols-2 gap-4" style={{ borderTop: "1px solid var(--border)" }}>
              <div>
                <p className="text-xs font-medium mb-2" style={{ color: "var(--status-good)" }}>
                  You already have
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {have.map((s) => (
                    <span
                      key={s.skill}
                      className="text-xs rounded-full px-2.5 py-1"
                      style={{ background: "color-mix(in srgb, var(--status-good) 14%, var(--surface-1))", color: "var(--status-good)" }}
                    >
                      {s.skill} · {s.demand_count}
                    </span>
                  ))}
                  {have.length === 0 && <span className="text-xs" style={{ color: "var(--text-muted)" }}>None yet</span>}
                </div>
              </div>
              <div>
                <p className="text-xs font-medium mb-2" style={{ color: "var(--status-critical)" }}>
                  Missing, ranked by demand
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {missing.map((s) => (
                    <span
                      key={s.skill}
                      className="text-xs rounded-full px-2.5 py-1"
                      style={{ background: "color-mix(in srgb, var(--status-critical) 12%, var(--surface-1))", color: "var(--status-critical)" }}
                    >
                      {s.skill} · {s.demand_count}
                    </span>
                  ))}
                  {missing.length === 0 && <span className="text-xs" style={{ color: "var(--text-muted)" }}>Great coverage</span>}
                </div>
              </div>
            </div>
          )}
          {sampleSize !== undefined && (
            <p className="text-xs mt-3" style={{ color: "var(--text-muted)" }}>
              Based on {sampleSize} matching posting{sampleSize === 1 ? "" : "s"} in the database.
            </p>
          )}
        </AIToolResultCard>
      </div>
    </PageTransition>
  );
}
