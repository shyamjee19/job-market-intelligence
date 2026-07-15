import { Menu } from "lucide-react";
import { useState } from "react";
import { Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Navbar } from "./Navbar";
import { NotificationBell } from "./NotificationBell";
import { Sidebar } from "./Sidebar";
import { ThemeToggle } from "./ThemeToggle";
import { UserMenu } from "./UserMenu";

export function AppLayout() {
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!user) {
    return (
      <>
        <Navbar />
        <Outlet />
      </>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />

      <div className="flex-1 min-w-0 flex flex-col">
        <header
          className="sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 py-3"
          style={{
            background: "color-mix(in srgb, var(--page-plane) 82%, transparent)",
            backdropFilter: "blur(10px)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          <button
            className="sm:hidden p-1.5 rounded-md"
            style={{ color: "var(--text-secondary)" }}
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={19} />
          </button>
          <div className="hidden sm:block" />

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <NotificationBell />
            <UserMenu />
          </div>
        </header>

        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
