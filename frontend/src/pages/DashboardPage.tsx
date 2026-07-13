import {
  AlertTriangle,
  Briefcase,
  Building2,
  DollarSign,
  Globe,
  Shuffle,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchHiringMap,
  fetchPostingsByDate,
  fetchSalaryDistribution,
  fetchSources,
  fetchSummary,
  fetchTopCompanies,
  fetchTopTags,
  fetchTrend,
} from "../api/client";
import { AreaChart } from "../components/AreaChart";
import { BarChart } from "../components/BarChart";
import { ColumnChart } from "../components/ColumnChart";
import { PageTransition } from "../components/PageTransition";
import { StatTile } from "../components/StatTile";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { SkeletonChart, SkeletonStatTile } from "../components/ui/Skeleton";
import { WorldMap } from "../components/WorldMap";
import { formatSource } from "../lib/format";
import type { CountByLabel, HiringTrend, PostingsByDate, SalaryBucket, SummaryStats } from "../types";

function formatSalaryBucketLabel(bucket: SalaryBucket): string {
  return `$${bucket.bucket_start / 1000}k`;
}

export function DashboardPage() {
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [companies, setCompanies] = useState<CountByLabel[]>([]);
  const [topSkills, setTopSkills] = useState<CountByLabel[]>([]);
  const [aiSkills, setAiSkills] = useState<CountByLabel[]>([]);
  const [cloudSkills, setCloudSkills] = useState<CountByLabel[]>([]);
  const [techSkills, setTechSkills] = useState<CountByLabel[]>([]);
  const [postings, setPostings] = useState<PostingsByDate[]>([]);
  const [salary, setSalary] = useState<SalaryBucket[]>([]);
  const [sources, setSources] = useState<CountByLabel[]>([]);
  const [hiringMap, setHiringMap] = useState<CountByLabel[]>([]);
  const [trend, setTrend] = useState<HiringTrend | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      fetchSummary(),
      fetchTopCompanies(8),
      fetchTopTags(8),
      fetchTopTags(6, "ai"),
      fetchTopTags(6, "cloud"),
      fetchTopTags(6, "tech"),
      fetchPostingsByDate(),
      fetchSalaryDistribution(),
      fetchSources(),
      fetchHiringMap(),
      fetchTrend(),
    ])
      .then(([s, c, top, ai, cloud, tech, p, sal, src, map, tr]) => {
        setSummary(s);
        setCompanies(c);
        setTopSkills(top);
        setAiSkills(ai);
        setCloudSkills(cloud);
        setTechSkills(tech);
        setPostings(p);
        setSalary(sal);
        setSources(src);
        setHiringMap(map);
        setTrend(tr);
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

  const trendPositive = (trend?.pct_change ?? 0) >= 0;

  return (
    <PageTransition>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Market dashboard
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          A snapshot of the job market across {sources.length || "all"} source
          {sources.length === 1 ? "" : "s"}, refreshed on every collector run.
        </p>

        <div className="flex flex-wrap gap-3 mb-6">
          {loading || !summary ? (
            <>
              <SkeletonStatTile />
              <SkeletonStatTile />
              <SkeletonStatTile />
              <SkeletonStatTile />
              <SkeletonStatTile />
              <SkeletonStatTile />
            </>
          ) : (
            <>
              <StatTile
                label="Total jobs"
                value={summary.total_jobs.toLocaleString()}
                icon={Briefcase}
                colorVar="--series-blue"
              />
              <StatTile
                label="Remote"
                value={summary.remote_jobs.toLocaleString()}
                icon={Globe}
                colorVar="--series-aqua"
              />
              <StatTile
                label="Hybrid"
                value={summary.hybrid_jobs.toLocaleString()}
                icon={Shuffle}
                colorVar="--series-violet"
              />
              <StatTile
                label="Onsite"
                value={summary.onsite_jobs.toLocaleString()}
                icon={Building2}
                colorVar="--series-orange"
              />
              <StatTile
                label="Avg salary"
                value={
                  summary.avg_salary_min && summary.avg_salary_max
                    ? `$${Math.round(summary.avg_salary_min / 1000)}k–${Math.round(summary.avg_salary_max / 1000)}k`
                    : "—"
                }
                icon={DollarSign}
                colorVar="--series-green"
              />
              <StatTile
                label="Trend vs yesterday"
                value={trend?.pct_change !== null && trend?.pct_change !== undefined ? `${trendPositive ? "+" : ""}${trend.pct_change}%` : "—"}
                icon={trendPositive ? TrendingUp : TrendingDown}
                colorVar={trendPositive ? "--status-good" : "--status-critical"}
              />
            </>
          )}
        </div>

        <Card hoverable className="p-5 mb-5">
          {loading ? (
            <SkeletonChart />
          ) : (
            <AreaChart
              data={postings.map((p) => ({ date: p.date, count: p.count }))}
              color="var(--series-blue)"
              title="Hiring trend"
            />
          )}
        </Card>

        <div className="grid gap-5 md:grid-cols-2 mb-5">
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={companies} color="var(--series-blue)" title="Top companies" />}
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

        <Card hoverable className="p-5 mb-5">
          {loading ? <SkeletonChart /> : <WorldMap data={hiringMap} totalJobs={summary?.total_jobs ?? 0} />}
        </Card>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4 mb-5">
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={topSkills} color="var(--series-blue)" title="Top skills" />}
          </Card>
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={aiSkills} color="var(--series-magenta)" title="AI skills" />}
          </Card>
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={cloudSkills} color="var(--series-aqua)" title="Cloud skills" />}
          </Card>
          <Card hoverable className="p-5">
            {loading ? <SkeletonChart /> : <BarChart data={techSkills} color="var(--series-orange)" title="Tech trends" />}
          </Card>
        </div>

        <Card hoverable className="p-5">
          {loading ? (
            <SkeletonChart />
          ) : (
            <BarChart
              data={sources.map((s) => ({ label: formatSource(s.label), count: s.count }))}
              color="var(--series-green)"
              title="Postings by source"
            />
          )}
        </Card>
      </div>
    </PageTransition>
  );
}
