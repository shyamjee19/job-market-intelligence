import { AlertTriangle, MapPin, Search, SearchX, Tag as TagIcon, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchJobs } from "../api/client";
import { PageTransition } from "../components/PageTransition";
import { Pagination } from "../components/Pagination";
import { TagBadge } from "../components/TagBadge";
import { Avatar } from "../components/ui/Avatar";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Input } from "../components/ui/Input";
import { SkeletonTableRows } from "../components/ui/Skeleton";
import { formatDate, formatSalary } from "../lib/format";
import type { JobSummary } from "../types";

const PAGE_SIZE = 20;

export function JobsListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [location, setLocation] = useState("");
  const [tag, setTag] = useState("");
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<JobSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    setPage(1);
  }, [search, location, tag]);

  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(() => {
      setLoading(true);
      setError(null);
      fetchJobs({ search, location, tag, page, page_size: PAGE_SIZE })
        .then((res) => {
          if (cancelled) return;
          setItems(res.items);
          setTotal(res.total);
        })
        .catch((err) => {
          if (!cancelled) setError(err.message ?? "Failed to load jobs");
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [search, location, tag, page, requestId]);

  const activeFilters = [
    search && { key: "search", label: `"${search}"`, clear: () => setSearch("") },
    location && { key: "location", label: location, clear: () => setLocation("") },
    tag && { key: "tag", label: tag, clear: () => setTag("") },
  ].filter(Boolean) as { key: string; label: string; clear: () => void }[];

  const hasFilters = activeFilters.length > 0;

  return (
    <PageTransition>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-end justify-between mb-6 flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>
              Job postings
            </h1>
            <p className="text-sm mt-1 tabular" style={{ color: "var(--text-secondary)" }}>
              {loading
                ? "Loading…"
                : `${total.toLocaleString()} open roles${hasFilters ? " matching your filters" : " tracked from RemoteOK"}`}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-3">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onClear={() => setSearch("")}
            placeholder="Search position, company, description…"
            icon={<Search size={15} />}
            className="flex-1 min-w-[240px]"
          />
          <Input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onClear={() => setLocation("")}
            placeholder="Location"
            icon={<MapPin size={15} />}
            className="w-44"
          />
          <Input
            value={tag}
            onChange={(e) => setTag(e.target.value)}
            onClear={() => setTag("")}
            placeholder="Tag"
            icon={<TagIcon size={15} />}
            className="w-40"
          />
        </div>

        {hasFilters && (
          <div className="flex flex-wrap items-center gap-2 mb-5">
            {activeFilters.map((f) => (
              <button
                key={f.key}
                onClick={f.clear}
                className="flex items-center gap-1 rounded-full pl-3 pr-2 py-1 text-xs font-medium transition-colors duration-150 hover:brightness-95"
                style={{
                  background: "color-mix(in srgb, var(--series-blue) 12%, var(--surface-1))",
                  color: "var(--series-blue)",
                  border: "1px solid color-mix(in srgb, var(--series-blue) 25%, transparent)",
                }}
              >
                {f.label}
                <X size={12} />
              </button>
            ))}
            <button
              onClick={() => {
                setSearch("");
                setLocation("");
                setTag("");
              }}
              className="text-xs font-medium px-2 py-1"
              style={{ color: "var(--text-muted)" }}
            >
              Clear all
            </button>
          </div>
        )}

        {error ? (
          <Card className="flex flex-col items-center gap-3 py-16 text-center">
            <AlertTriangle size={28} style={{ color: "var(--status-critical)" }} />
            <div>
              <p className="font-medium" style={{ color: "var(--text-primary)" }}>
                Couldn't load jobs
              </p>
              <p className="text-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>
                {error}
              </p>
            </div>
            <Button onClick={() => setRequestId((n) => n + 1)}>Retry</Button>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}>
                    <th className="text-left font-medium px-4 py-2.5">Position</th>
                    <th className="text-left font-medium px-4 py-2.5">Location</th>
                    <th className="text-left font-medium px-4 py-2.5">Salary</th>
                    <th className="text-left font-medium px-4 py-2.5">Tags</th>
                    <th className="text-left font-medium px-4 py-2.5">Posted</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <SkeletonTableRows rows={10} />
                  ) : items.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-16">
                        <div className="flex flex-col items-center gap-2 text-center">
                          <SearchX size={26} style={{ color: "var(--text-muted)" }} />
                          <p style={{ color: "var(--text-secondary)" }}>No jobs match your filters.</p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    items.map((job) => (
                      <tr
                        key={job.job_id}
                        onClick={() => navigate(`/jobs/${job.job_id}`)}
                        className="cursor-pointer transition-colors duration-100 hover:bg-black/[0.02] dark:hover:bg-white/[0.03]"
                        style={{ borderTop: "1px solid var(--border)" }}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <Avatar name={job.company ?? "?"} />
                            <div className="min-w-0">
                              <div className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                                {job.position}
                              </div>
                              <div className="text-xs truncate" style={{ color: "var(--text-secondary)" }}>
                                {job.company}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>
                          {job.location ?? "—"}
                        </td>
                        <td className="px-4 py-3 tabular">
                          <span
                            className="rounded-full px-2 py-0.5 text-xs font-medium"
                            style={{
                              background:
                                job.salary_min || job.salary_max
                                  ? "color-mix(in srgb, var(--status-good) 14%, var(--surface-1))"
                                  : "var(--surface-2)",
                              color: job.salary_min || job.salary_max ? "var(--status-good)" : "var(--text-muted)",
                            }}
                          >
                            {formatSalary(job.salary_min, job.salary_max)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1 max-w-[240px]">
                            {job.tags.slice(0, 2).map((t) => (
                              <TagBadge
                                key={t}
                                tag={t}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setTag(t);
                                }}
                              />
                            ))}
                            {job.tags.length > 2 && (
                              <span className="text-xs self-center" style={{ color: "var(--text-muted)" }}>
                                +{job.tags.length - 2}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 tabular whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>
                          {formatDate(job.date_posted)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {!error && <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />}
      </div>
    </PageTransition>
  );
}
