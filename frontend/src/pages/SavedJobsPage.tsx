import { AlertTriangle, Bookmark, Building2, Heart, SearchX } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchFavoriteCompanies, fetchSavedJobs, unfavoriteCompany, unsaveJob } from "../api/userClient";
import { PageTransition } from "../components/PageTransition";
import { SourceBadge } from "../components/SourceBadge";
import { Avatar } from "../components/ui/Avatar";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { formatDate, formatSalary } from "../lib/format";
import type { FavoriteCompany, JobSummary } from "../types";

export function SavedJobsPage() {
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);
  const [companies, setCompanies] = useState<FavoriteCompany[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([fetchSavedJobs(), fetchFavoriteCompanies()])
      .then(([j, c]) => {
        setJobs(j);
        setCompanies(c);
      })
      .catch((err) => setError(err.message ?? "Failed to load saved items"));
  }, []);

  async function removeJob(jobId: number) {
    setJobs((prev) => prev?.filter((j) => j.id !== jobId) ?? null);
    await unsaveJob(jobId).catch(() => {});
  }

  async function removeCompany(name: string) {
    setCompanies((prev) => prev?.filter((c) => c.company_name !== name) ?? null);
    await unfavoriteCompany(name).catch(() => {});
  }

  const loading = jobs === null || companies === null;

  return (
    <PageTransition>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-semibold mb-6" style={{ color: "var(--text-primary)" }}>
          Saved
        </h1>

        {error && (
          <Card className="flex items-center gap-2 p-4 mb-6" style={{ color: "var(--status-critical)" }}>
            <AlertTriangle size={16} />
            <span className="text-sm">{error}</span>
          </Card>
        )}

        <section className="mb-8">
          <h2 className="flex items-center gap-2 text-sm font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>
            <Bookmark size={15} />
            Saved jobs {jobs && `(${jobs.length})`}
          </h2>

          {loading ? (
            <div className="space-y-2">
              <Skeleton className="h-16 w-full rounded-xl" />
              <Skeleton className="h-16 w-full rounded-xl" />
            </div>
          ) : jobs.length === 0 ? (
            <Card className="flex flex-col items-center gap-2 py-10 text-center">
              <SearchX size={22} style={{ color: "var(--text-muted)" }} />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                No saved jobs yet. Bookmark a listing to see it here.
              </p>
            </Card>
          ) : (
            <div className="flex flex-col gap-2">
              {jobs.map((job) => (
                <Card key={job.id} className="flex items-center gap-3 p-3.5">
                  <Avatar name={job.company ?? "?"} />
                  <Link to={`/jobs/${job.id}`} className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                        {job.position}
                      </span>
                      <SourceBadge source={job.source} />
                    </div>
                    <div className="text-xs mt-0.5 truncate" style={{ color: "var(--text-secondary)" }}>
                      {job.company} · {job.location ?? "—"} · {formatSalary(job.salary_min, job.salary_max)} · Posted{" "}
                      {formatDate(job.date_posted)}
                    </div>
                  </Link>
                  <Button size="sm" onClick={() => removeJob(job.id)}>
                    Remove
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </section>

        <section>
          <h2 className="flex items-center gap-2 text-sm font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>
            <Heart size={15} />
            Followed companies {companies && `(${companies.length})`}
          </h2>

          {loading ? (
            <Skeleton className="h-14 w-full rounded-xl" />
          ) : companies.length === 0 ? (
            <Card className="flex flex-col items-center gap-2 py-10 text-center">
              <Building2 size={22} style={{ color: "var(--text-muted)" }} />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Follow a company from a job listing to track them here.
              </p>
            </Card>
          ) : (
            <div className="flex flex-col gap-2">
              {companies.map((c) => (
                <Card key={c.company_key} className="flex items-center gap-3 p-3.5">
                  <Avatar name={c.company_name} />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                      {c.company_name}
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: "var(--text-secondary)" }}>
                      Following since {formatDate(c.favorited_at)}
                    </div>
                  </div>
                  <Button size="sm" onClick={() => removeCompany(c.company_name)}>
                    Unfollow
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </section>
      </div>
    </PageTransition>
  );
}
