import DOMPurify from "dompurify";
import { AlertTriangle, ArrowLeft, Calendar, ExternalLink, MapPin, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchJob } from "../api/client";
import { PageTransition } from "../components/PageTransition";
import { SourceBadge } from "../components/SourceBadge";
import { TagBadge } from "../components/TagBadge";
import { Avatar } from "../components/ui/Avatar";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { formatDate, formatSalary } from "../lib/format";
import type { JobDetail } from "../types";

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);
    setError(null);
    fetchJob(Number(jobId))
      .then(setJob)
      .catch((err) => setError(err.message ?? "Failed to load job"))
      .finally(() => setLoading(false));
  }, [jobId]);

  return (
    <PageTransition>
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-sm mb-5 transition-colors duration-150 hover:text-[var(--text-primary)]"
          style={{ color: "var(--text-secondary)" }}
        >
          <ArrowLeft size={15} />
          Back to jobs
        </Link>

        {loading && (
          <Card className="p-6">
            <div className="flex items-center gap-3">
              <Skeleton className="h-12 w-12 rounded-full" />
              <div className="flex-1">
                <Skeleton className="h-5 w-56 mb-2" />
                <Skeleton className="h-4 w-32" />
              </div>
            </div>
            <div className="flex gap-4 mt-5">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-24" />
            </div>
            <Skeleton className="h-9 w-32 mt-5 rounded-lg" />
            <div className="mt-6 pt-6 space-y-2" style={{ borderTop: "1px solid var(--border)" }}>
              <Skeleton className="h-3.5 w-full" />
              <Skeleton className="h-3.5 w-full" />
              <Skeleton className="h-3.5 w-3/4" />
            </div>
          </Card>
        )}

        {error && (
          <Card className="flex flex-col items-center gap-3 py-16 text-center">
            <AlertTriangle size={28} style={{ color: "var(--status-critical)" }} />
            <div>
              <p className="font-medium" style={{ color: "var(--text-primary)" }}>
                Couldn't load this job
              </p>
              <p className="text-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>
                {error}
              </p>
            </div>
            <Link to="/">
              <Button>Back to jobs</Button>
            </Link>
          </Card>
        )}

        {job && !loading && (
          <Card className="p-6">
            <div className="flex items-center gap-3.5">
              <Avatar name={job.company ?? "?"} size={48} />
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
                    {job.position}
                  </h1>
                  <SourceBadge source={job.source} />
                </div>
                <p className="text-[15px] mt-0.5" style={{ color: "var(--text-secondary)" }}>
                  {job.company}
                </p>
              </div>
            </div>

            <div
              className="flex flex-wrap gap-x-5 gap-y-2 mt-5 text-sm tabular"
              style={{ color: "var(--text-secondary)" }}
            >
              <span className="flex items-center gap-1.5">
                <MapPin size={14} style={{ color: "var(--text-muted)" }} />
                {job.location ?? "Location not specified"}
                {job.remote_type && ` · ${job.remote_type === "remote" ? "Remote" : "Onsite"}`}
              </span>
              <span className="flex items-center gap-1.5">
                <Wallet size={14} style={{ color: "var(--text-muted)" }} />
                {formatSalary(job.salary_min, job.salary_max)}
              </span>
              <span className="flex items-center gap-1.5">
                <Calendar size={14} style={{ color: "var(--text-muted)" }} />
                Posted {formatDate(job.date_posted)}
              </span>
            </div>

            {job.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-4">
                {job.tags.map((t) => (
                  <TagBadge key={t} tag={t} />
                ))}
              </div>
            )}

            {job.apply_url && (
              <a href={job.apply_url} target="_blank" rel="noreferrer" className="inline-block mt-5">
                <Button variant="primary">
                  Apply now
                  <ExternalLink size={14} />
                </Button>
              </a>
            )}

            {job.description && (
              <div
                className="mt-6 pt-6 text-sm leading-relaxed job-description"
                style={{ borderTop: "1px solid var(--border)", color: "var(--text-primary)" }}
                // job.description is third-party, company-submitted HTML from whichever
                // source this posting came from - never trust it as-is. DOMPurify strips
                // scripts/handlers before it hits the DOM.
                dangerouslySetInnerHTML={{
                  __html: DOMPurify.sanitize(job.description, {
                    ALLOWED_TAGS: ["p", "br", "b", "strong", "i", "em", "ul", "ol", "li", "a"],
                    ALLOWED_ATTR: ["href"],
                  }),
                }}
              />
            )}
          </Card>
        )}
      </div>
    </PageTransition>
  );
}
