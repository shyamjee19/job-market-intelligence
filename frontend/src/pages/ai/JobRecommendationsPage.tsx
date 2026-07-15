import { Wand2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getJobRecommendations } from "../../api/aiToolsClient";
import { AIToolResultCard } from "../../components/AIToolResultCard";
import { PageTransition } from "../../components/PageTransition";
import { Card } from "../../components/ui/Card";
import type { AIToolResponse } from "../../types";

interface RecommendedJob {
  id: number;
  position: string | null;
  company: string | null;
  location: string | null;
}

export function JobRecommendationsPage() {
  const [result, setResult] = useState<AIToolResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJobRecommendations()
      .then(setResult)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load recommendations"))
      .finally(() => setLoading(false));
  }, []);

  const jobs = (result?.data?.jobs as RecommendedJob[] | undefined) ?? [];

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          <Wand2 size={22} style={{ color: "var(--series-violet)" }} />
          AI Job Recommendations
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Postings ranked by overlap with your profile skills — add skills on your profile to improve these.
        </p>

        <AIToolResultCard loading={loading} error={error} summary={result?.summary ?? null}>
          {jobs.length > 0 && (
            <div className="mt-4 pt-4 flex flex-col gap-2" style={{ borderTop: "1px solid var(--border)" }}>
              {jobs.map((j) => (
                <Link key={j.id} to={`/jobs/${j.id}`}>
                  <Card hoverable className="p-3.5">
                    <p className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                      {j.position}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
                      {j.company} · {j.location ?? "Location not specified"}
                    </p>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </AIToolResultCard>
      </div>
    </PageTransition>
  );
}
