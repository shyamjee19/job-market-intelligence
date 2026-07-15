import { BarChart3, Bookmark, Briefcase, Sparkles } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";

const navItems = [
  { to: "/", label: "Jobs", icon: Briefcase, end: true },
  { to: "/dashboard", label: "Dashboard", icon: BarChart3, end: false },
  { to: "/assistant", label: "Assistant", icon: Sparkles, end: false },
];

export function Navbar() {
  const { user } = useAuth();

  return (
    <header
      className="sticky top-0 z-30"
      style={{
        background: "color-mix(in srgb, var(--page-plane) 82%, transparent)",
        backdropFilter: "blur(10px)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div
              className="flex items-center justify-center rounded-lg w-7 h-7 text-white font-bold text-sm"
              style={{ background: "var(--series-blue)" }}
            >
              J
            </div>
            <span className="font-semibold text-[15px] tracking-tight" style={{ color: "var(--text-primary)" }}>
              Job Market Intelligence
            </span>
          </div>

          <nav className="hidden sm:flex items-center gap-1">
            {navItems.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-150"
                style={({ isActive }) => ({
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  background: isActive ? "var(--surface-2)" : "transparent",
                })}
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
            {user && (
              <NavLink
                to="/saved"
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-150"
                style={({ isActive }) => ({
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  background: isActive ? "var(--surface-2)" : "transparent",
                })}
              >
                <Bookmark size={15} />
                Saved
              </NavLink>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
