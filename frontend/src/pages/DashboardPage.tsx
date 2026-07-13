import { AlertTriangle, Briefcase, Building2, DollarSign, MapPinned } from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchPostingsByDate,
  fetchSalaryDistribution,
  fetchSummary,
  fetchTopCompanies,
  fetchTopTags,
} from "../api/client";
import { PageTransition } from "../components/PageTransition";
import { StatTile } from "../components/StatTile";
import { AreaChart } from "../components/AreaChart";
import { BarChart } from "../components/BarChart";
import { ColumnChart } from "../components/ColumnChart";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { SkeletonChart, SkeletonStatTile } from "../components/ui/Skeleton";
import type { CountByLabel, PostingsByDate, SalaryBucket, SummaryStats } from "../types";

function formatSalaryBucketLabel(bucket: SalaryBucket): string {
  return `$${bucket.bucket_start / 1000}k`;
}

export function DashboardPage() {
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [companies, setCompanies] = useState<CountByLabel[]>([]);
  const [tags, setTags] = useState<CountByLabel[]>([]);
  const [postings, setPostings] = useState<PostingsByDate[]>([]);
  const [salary, setSalary] = useState<SalaryBucket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchSummary(),
      fetchTopCompanies(8),
      fetchTopTags(10),
      fetchPostingsByDate(),
      fetchSalaryDistribution(),
    ])
      .then(([s, c, t, p, sal]) => {
        setSummary(s);
        setCompanies(c);
        setTags(t);
        setPostings(p);
        setSalary(sal);
      })
      .catch((err) => setError(err.message ?? "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, [requestId]);

  if (error) {
    return (
      <PageTransition>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
          <Card className="flex flex-col items-center gap-3 py-16 text-center">
            <AlertTriangle size={28} style={{ color: "var(--status-critical)" }} />
            <div>
              <p className="font-medium" style={{ color: "var(--text-primary)" }}>
                Couldn't load the dashboard
              </p>
              <p className="text-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>
                {error}
              </p>
            </div>
            <Button onClick={() => setRequestId((n) => n + 1)}>Retry</Button>
          </Card>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Market dashboard
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          A snapshot of the remote job market, refreshed on every collector run.
        </p>

        <div className="flex flex-wrap gap-3 mb-6">
          {loading || !summary ? (
            <>
              <SkeletonStatTile />
              <SkeletonStatTile />
              <SkeletonStatTile />
              <SkeletonStatTile />
            </>
          ) : (
            <>
              <StatTile
                label="Total postings"
                value={summary.total_jobs.toLocaleString()}
                icon={Briefcase}
                colorVar="--series-blue"
              />
              <StatTile
                label="Companies hiring"
                value={summary.total_companies.toLocaleString()}
                icon={Building2}
                colorVar="--series-aqua"
              />
              <StatTile
                label="Locations"
                value={summary.total_locations.toLocaleString()}
                icon={MapPinned}
                colorVar="--series-violet"
              />
              <StatTile
                label="Avg salary range"
                value={
                  summary.avg_salary_min && summary.avg_salary_max
                    ? `$${Math.round(summary.avg_salary_min / 1000)}k–${Math.round(summary.avg_salary_max / 1000)}k`
                    : "—"
                }
                icon={DollarSign}
                colorVar="--series-orange"
              />
            </>
          )}
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={companies} color="var(--series-blue)" title="Top companies by postings" />}
          </Card>
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={tags} color="var(--series-aqua)" title="Top skills / tags" />}
          </Card>
          <Card hoverable className="p-5">
            {loading ? (
              <SkeletonChart />
            ) : (
              <AreaChart
                data={postings.map((p) => ({ date: p.date, count: p.count }))}
                color="var(--series-blue)"
                title="Postings over time"
              />
            )}
          </Card>
          <Card hoverable className="p-5">
            {loading ? (
              <SkeletonChart />
            ) : (
              <ColumnChart
                data={salary.map((b) => ({ label: formatSalaryBucketLabel(b), count: b.count }))}
                color="var(--series-violet)"
                title="Salary distribution (min salary, $20k bands)"
              />
            )}
          </Card>
        </div>
      </div>
    </PageTransition>
  );
}
