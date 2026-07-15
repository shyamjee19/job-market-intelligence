import { Link } from "react-router-dom";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";

// Rendered only for logged-out visitors, and only on the auth pages
// (login/register/forgot-password/reset-password/oauth-callback) - every
// other route requires a session (see App.tsx / ProtectedRoute), so there's
// no functional nav to show here, just the brand and the way back in.
export function Navbar() {
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
        <Link to="/" className="flex items-center gap-2">
          <div
            className="flex items-center justify-center rounded-lg w-7 h-7 text-white font-bold text-sm"
            style={{ background: "var(--series-blue)" }}
          >
            J
          </div>
          <span className="font-semibold text-[15px] tracking-tight" style={{ color: "var(--text-primary)" }}>
            JobPulse
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
