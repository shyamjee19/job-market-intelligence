import { LayoutDashboard, LogOut, Settings, User as UserIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui/Button";

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Button size="sm" onClick={() => navigate("/login")}>
          Sign in
        </Button>
        <Button size="sm" variant="primary" onClick={() => navigate("/register")}>
          Sign up
        </Button>
      </div>
    );
  }

  const initial = (user.full_name ?? user.email)[0]?.toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center justify-center rounded-full w-8 h-8 text-sm font-semibold text-white"
        style={{ background: "var(--series-violet)" }}
      >
        {initial}
      </button>

      {open && (
        <div
          className="absolute right-0 mt-2 w-48 rounded-lg overflow-hidden z-40"
          style={{ background: "var(--surface-1)", border: "1px solid var(--border)", boxShadow: "var(--shadow-lg)" }}
        >
          <div className="px-3 py-2.5 text-sm truncate" style={{ borderBottom: "1px solid var(--border)", color: "var(--text-secondary)" }}>
            {user.email}
          </div>
          <button
            onClick={() => {
              setOpen(false);
              navigate("/profile");
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-black/5 dark:hover:bg-white/5"
            style={{ color: "var(--text-primary)" }}
          >
            <UserIcon size={14} />
            Profile & alerts
          </button>
          <button
            onClick={() => {
              setOpen(false);
              navigate("/settings");
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-black/5 dark:hover:bg-white/5"
            style={{ color: "var(--text-primary)" }}
          >
            <Settings size={14} />
            Settings
          </button>
          {user.role === "admin" && (
            <button
              onClick={() => {
                setOpen(false);
                navigate("/admin");
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-black/5 dark:hover:bg-white/5"
              style={{ color: "var(--text-primary)" }}
            >
              <LayoutDashboard size={14} />
              Admin dashboard
            </button>
          )}
          <button
            onClick={async () => {
              setOpen(false);
              await logout();
              // A hard redirect, not react-router's navigate(): every other
              // page on this route is now behind ProtectedRoute, and
              // AnimatePresence keeps the outgoing (still-protected) page
              // mounted during its exit transition - long enough for its
              // own guard to notice user is now null and race a redirect
              // to /login against this one. A full reload sidesteps that
              // entirely by discarding the old tree instead of racing it.
              window.location.replace("/");
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-black/5 dark:hover:bg-white/5"
            style={{ color: "var(--status-critical)" }}
          >
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
