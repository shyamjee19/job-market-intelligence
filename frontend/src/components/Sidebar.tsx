import {
  Bell,
  BookOpen,
  Bookmark,
  BriefcaseBusiness,
  Compass,
  DollarSign,
  FileText,
  LayoutDashboard,
  MessageSquareText,
  Settings as SettingsIcon,
  ShieldCheck,
  Sparkles,
  Target,
  User as UserIcon,
  Wand2,
  X,
} from "lucide-react";
import type { ComponentType } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface NavItem {
  to: string;
  label: string;
  icon: ComponentType<{ size?: number }>;
}

const MAIN_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { to: "/assistant", label: "AI Chat", icon: Sparkles },
  { to: "/saved", label: "Saved Jobs", icon: Bookmark },
];

const AI_TOOL_ITEMS: NavItem[] = [
  { to: "/ai/resume-analyzer", label: "Resume Analyzer", icon: FileText },
  { to: "/ai/career-advisor", label: "Career Advisor", icon: Compass },
  { to: "/ai/skill-gap", label: "Skill Gap Analysis", icon: Target },
  { to: "/ai/salary-insights", label: "Salary Insights", icon: DollarSign },
  { to: "/ai/job-recommendations", label: "Job Recommendations", icon: Wand2 },
  { to: "/ai/interview-prep", label: "Interview Prep", icon: MessageSquareText },
];

const ACCOUNT_ITEMS: NavItem[] = [
  { to: "/profile", label: "Profile", icon: UserIcon },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

function NavGroup({ title, items, onNavigate }: { title: string; items: NavItem[]; onNavigate?: () => void }) {
  return (
    <div className="mb-5">
      <p className="px-3 mb-1.5 text-[11px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
        {title}
      </p>
      <nav className="flex flex-col gap-0.5">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onNavigate}
            className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-150"
            style={({ isActive }) => ({
              color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
              background: isActive ? "var(--surface-2)" : "transparent",
            })}
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

export function Sidebar({ mobileOpen, onClose }: { mobileOpen: boolean; onClose: () => void }) {
  const { user } = useAuth();

  return (
    <>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 sm:hidden" onClick={onClose} aria-hidden />
      )}

      <aside
        className={`fixed sm:sticky top-0 z-50 sm:z-auto h-screen w-64 shrink-0 flex flex-col transition-transform duration-200 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full sm:translate-x-0"
        }`}
        style={{ background: "var(--surface-1)", borderRight: "1px solid var(--border)" }}
      >
        <div className="flex items-center justify-between px-4 py-4">
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
          <button className="sm:hidden p-1 rounded-md" style={{ color: "var(--text-secondary)" }} onClick={onClose} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2">
          <NavGroup title="Overview" items={MAIN_ITEMS} onNavigate={onClose} />
          <NavGroup title="AI Tools" items={AI_TOOL_ITEMS} onNavigate={onClose} />
          <NavGroup title="Account" items={ACCOUNT_ITEMS} onNavigate={onClose} />
          {user?.role === "admin" && (
            <NavGroup title="Admin" items={[{ to: "/admin", label: "Admin Dashboard", icon: ShieldCheck }]} onNavigate={onClose} />
          )}
        </div>

        <div className="px-4 py-3 text-xs flex items-center gap-1.5" style={{ color: "var(--text-muted)", borderTop: "1px solid var(--border)" }}>
          <BookOpen size={13} />
          JobPulse · AI-powered job intelligence
        </div>
      </aside>
    </>
  );
}
