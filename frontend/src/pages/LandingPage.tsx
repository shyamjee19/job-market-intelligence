import {
  ArrowRight,
  BarChart3,
  Bell,
  Bookmark,
  Briefcase,
  Building2,
  Compass,
  FileText,
  Globe,
  Send,
  Sparkles,
  Target,
  TrendingUp,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSummary, fetchTopTags } from "../api/client";
import { ThemeToggle } from "../components/ThemeToggle";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import type { CountByLabel, SummaryStats } from "../types";

const FEATURES = [
  {
    icon: BarChart3,
    title: "Live market dashboard",
    description: "Hiring trends, top companies, salary bands, and a world hiring map built from real postings.",
  },
  {
    icon: Sparkles,
    title: "AI chat assistant",
    description: "Ask questions about the job market and get answers grounded in — and cited from — real postings.",
  },
  {
    icon: FileText,
    title: "AI resume analyzer",
    description: "Get structured feedback on your resume against the skills actually in demand right now.",
  },
  {
    icon: Compass,
    title: "AI career advisor",
    description: "A concrete roadmap toward your next role, grounded in real postings that match your goal.",
  },
  {
    icon: Target,
    title: "Skill gap analysis",
    description: "See exactly which in-demand skills you're missing for a target role, ranked by real demand.",
  },
  {
    icon: Bell,
    title: "Job alerts",
    description: "Save a search once and get notified the moment a new posting matches your criteria.",
  },
];

function TopBar() {
  return (
    <header className="max-w-6xl mx-auto px-4 sm:px-6 py-5 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div
          className="flex items-center justify-center rounded-lg w-7 h-7 text-white font-bold text-sm"
          style={{ background: "var(--series-blue)" }}
        >
          J
        </div>
        <span className="font-semibold text-[15px] tracking-tight" style={{ color: "var(--text-primary)" }}>
          JobPulse
        </span>
      </div>
      <div className="flex items-center gap-2">
        <ThemeToggle />
        <Link to="/login">
          <Button size="sm">Log in</Button>
        </Link>
        <Link to="/register">
          <Button size="sm" variant="primary">
            Get started
          </Button>
        </Link>
      </div>
    </header>
  );
}

function formatCompact(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}k`;
  return String(n);
}

export function LandingPage() {
  const [summary, setSummary] = useState<SummaryStats | null>(null);
  const [topSkills, setTopSkills] = useState<CountByLabel[]>([]);

  useEffect(() => {
    fetchSummary().then(setSummary).catch(() => {});
    fetchTopTags(6).then(setTopSkills).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen">
      <TopBar />

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pt-10 pb-16 text-center">
        <div
          className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium mb-5"
          style={{
            background: "color-mix(in srgb, var(--series-violet) 12%, var(--surface-1))",
            color: "var(--series-violet)",
            border: "1px solid color-mix(in srgb, var(--series-violet) 25%, transparent)",
          }}
        >
          <Sparkles size={12} />
          AI-powered job market intelligence
        </div>
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight leading-tight" style={{ color: "var(--text-primary)" }}>
          Understand the job market.
          <br />
          Land the right role faster.
        </h1>
        <p className="text-base sm:text-lg mt-5 max-w-2xl mx-auto" style={{ color: "var(--text-secondary)" }}>
          JobPulse pulls postings from multiple sources into one searchable dashboard, then layers on AI tools —
          resume review, career advice, skill gap analysis, salary insights — all grounded in real, current data.
        </p>
        <div className="flex items-center justify-center gap-3 mt-8">
          <Link to="/register">
            <Button variant="primary" size="md" className="px-5 py-2.5 text-[15px]">
              Get started free
              <ArrowRight size={16} />
            </Button>
          </Link>
          <Link to="/jobs">
            <Button size="md" className="px-5 py-2.5 text-[15px]">
              Browse jobs
            </Button>
          </Link>
        </div>
      </section>

      {/* Stats strip */}
      {summary && (
        <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-16">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard icon={Briefcase} label="Open roles tracked" value={formatCompact(summary.total_jobs)} />
            <StatCard icon={Building2} label="Companies hiring" value={formatCompact(summary.total_companies)} />
            <StatCard icon={Globe} label="Remote postings" value={formatCompact(summary.remote_jobs)} />
            <StatCard
              icon={Wallet}
              label="Avg. salary range"
              value={summary.avg_salary_min ? `$${Math.round(summary.avg_salary_min / 1000)}k+` : "—"}
            />
          </div>
        </section>
      )}

      {/* Live dashboard preview */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-16">
        <h2 className="text-2xl font-semibold text-center mb-2" style={{ color: "var(--text-primary)" }}>
          A dashboard with real signal
        </h2>
        <p className="text-center text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Not mock data — this preview is pulled live from the same postings powering the app.
        </p>
        <Card className="p-1.5 overflow-hidden">
          <div className="flex items-center gap-1.5 px-3 py-2" style={{ borderBottom: "1px solid var(--border)" }}>
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--status-critical)" }} />
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--status-warning, #eab308)" }} />
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: "var(--status-good)" }} />
            <span className="ml-3 text-xs" style={{ color: "var(--text-muted)" }}>
              jobpulse.app/dashboard
            </span>
          </div>
          <div className="p-5">
            {summary ? (
              <div className="grid sm:grid-cols-3 gap-3 mb-5">
                <StatCard icon={Briefcase} label="Total postings" value={summary.total_jobs.toLocaleString()} />
                <StatCard icon={TrendingUp} label="Posted today" value={String(summary.today_jobs)} />
                <StatCard icon={Globe} label="Remote share" value={`${Math.round((summary.remote_jobs / Math.max(summary.total_jobs, 1)) * 100)}%`} />
              </div>
            ) : (
              <div className="h-24 mb-5 rounded-lg animate-pulse" style={{ background: "var(--surface-2)" }} />
            )}
            {topSkills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topSkills.map((s) => (
                  <span
                    key={s.label}
                    className="text-xs font-medium rounded-full px-3 py-1.5"
                    style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}
                  >
                    {s.label} · {s.count}
                  </span>
                ))}
              </div>
            ) : (
              <div className="h-8 rounded-lg animate-pulse" style={{ background: "var(--surface-2)" }} />
            )}
          </div>
        </Card>
      </section>

      {/* AI assistant preview */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 pb-16">
        <h2 className="text-2xl font-semibold text-center mb-2" style={{ color: "var(--text-primary)" }}>
          Ask the market anything
        </h2>
        <p className="text-center text-sm mb-8" style={{ color: "var(--text-secondary)" }}>
          Every answer cites the postings it drew on — nothing invented.
        </p>
        <Card className="p-5">
          <div className="flex justify-end mb-3">
            <div className="rounded-xl px-4 py-2.5 max-w-[80%] text-sm" style={{ background: "var(--series-blue)", color: "#fff" }}>
              What skills are trending for backend roles right now?
            </div>
          </div>
          <div className="flex justify-start">
            <div
              className="rounded-xl px-4 py-2.5 max-w-[85%] text-sm leading-relaxed"
              style={{ background: "var(--surface-2)", color: "var(--text-primary)" }}
            >
              Based on current postings, Python, PostgreSQL, and AWS appear most frequently across backend roles,
              with growing mentions of Kubernetes and event-driven architecture.
              <div className="mt-2.5 pt-2.5 flex flex-wrap gap-1.5" style={{ borderTop: "1px solid var(--border)" }}>
                <span className="text-xs rounded-full px-2 py-0.5" style={{ background: "var(--surface-1)", color: "var(--text-secondary)" }}>
                  Backend Engineer · Acme Co
                </span>
                <span className="text-xs rounded-full px-2 py-0.5" style={{ background: "var(--surface-1)", color: "var(--text-secondary)" }}>
                  Platform Engineer · Nimbus
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <div
              className="flex-1 rounded-lg text-sm px-3.5 py-2.5"
              style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-muted)" }}
            >
              Ask about jobs, skills, companies, salaries…
            </div>
            <Button variant="primary" disabled>
              <Send size={15} />
            </Button>
          </div>
        </Card>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-16">
        <h2 className="text-2xl font-semibold text-center mb-8" style={{ color: "var(--text-primary)" }}>
          Everything you need in one place
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, description }) => (
            <Card key={title} hoverable className="p-5">
              <div
                className="flex items-center justify-center rounded-lg w-9 h-9 mb-3"
                style={{ background: "color-mix(in srgb, var(--series-blue) 12%, transparent)", color: "var(--series-blue)" }}
              >
                <Icon size={17} />
              </div>
              <h3 className="font-medium mb-1" style={{ color: "var(--text-primary)" }}>
                {title}
              </h3>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {description}
              </p>
            </Card>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 pb-20 text-center">
        <Card className="p-10">
          <Bookmark size={26} className="mx-auto mb-4" style={{ color: "var(--series-blue)" }} />
          <h2 className="text-2xl font-semibold mb-2" style={{ color: "var(--text-primary)" }}>
            Ready to get started?
          </h2>
          <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
            Create a free account — save jobs, follow companies, and unlock the AI tools.
          </p>
          <Link to="/register">
            <Button variant="primary" size="md" className="px-5 py-2.5 text-[15px]">
              Create your account
              <ArrowRight size={16} />
            </Button>
          </Link>
        </Card>
      </section>

      <footer className="max-w-6xl mx-auto px-4 sm:px-6 py-8 text-center text-xs" style={{ color: "var(--text-muted)" }}>
        JobPulse — AI-powered job market intelligence
      </footer>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: typeof Briefcase; label: string; value: string }) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-1.5" style={{ color: "var(--text-muted)" }}>
        <Icon size={13} />
        <span className="text-xs">{label}</span>
      </div>
      <div className="text-xl font-semibold tabular" style={{ color: "var(--text-primary)" }}>
        {value}
      </div>
    </Card>
  );
}
