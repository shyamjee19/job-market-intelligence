import { Bell } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchNotifications, fetchUnreadNotificationCount, markNotificationRead } from "../api/userClient";
import { formatDate } from "../lib/format";
import type { Notification } from "../types";

export function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [items, setItems] = useState<Notification[]>([]);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchUnreadNotificationCount()
      .then((r) => setUnreadCount(r.count))
      .catch(() => {});
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function toggleOpen() {
    if (!open) {
      fetchNotifications(1, 5)
        .then((res) => setItems(res.items))
        .catch(() => {});
    }
    setOpen((o) => !o);
  }

  async function handleClickNotification(n: Notification) {
    if (!n.is_read) {
      setItems((prev) => prev.map((x) => (x.notification_id === n.notification_id ? { ...x, is_read: true } : x)));
      setUnreadCount((c) => Math.max(0, c - 1));
      await markNotificationRead(n.notification_id).catch(() => {});
    }
    setOpen(false);
    navigate("/notifications");
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={toggleOpen}
        className="relative flex items-center justify-center w-8 h-8 rounded-full transition-colors duration-150 hover:bg-black/5 dark:hover:bg-white/10"
        style={{ color: "var(--text-secondary)" }}
        aria-label="Notifications"
      >
        <Bell size={17} />
        {unreadCount > 0 && (
          <span
            className="absolute top-0.5 right-0.5 flex items-center justify-center rounded-full text-[10px] font-semibold text-white"
            style={{ background: "var(--status-critical)", minWidth: 14, height: 14, padding: "0 3px" }}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 mt-2 w-80 rounded-lg overflow-hidden z-40"
          style={{ background: "var(--surface-1)", border: "1px solid var(--border)", boxShadow: "var(--shadow-lg)" }}
        >
          <div className="px-3.5 py-2.5 text-sm font-medium" style={{ borderBottom: "1px solid var(--border)", color: "var(--text-primary)" }}>
            Notifications
          </div>
          {items.length === 0 ? (
            <p className="px-3.5 py-6 text-sm text-center" style={{ color: "var(--text-secondary)" }}>
              You're all caught up.
            </p>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              {items.map((n) => (
                <button
                  key={n.notification_id}
                  onClick={() => handleClickNotification(n)}
                  className="w-full text-left px-3.5 py-2.5 text-sm transition-colors duration-100 hover:bg-black/[0.03] dark:hover:bg-white/[0.04]"
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <div className="flex items-start gap-2">
                    {!n.is_read && (
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0" style={{ background: "var(--series-blue)" }} />
                    )}
                    <div className="min-w-0">
                      <p className="font-medium truncate" style={{ color: "var(--text-primary)" }}>
                        {n.subject ?? "Notification"}
                      </p>
                      <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {formatDate(n.created_at)}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
          <button
            onClick={() => {
              setOpen(false);
              navigate("/notifications");
            }}
            className="w-full text-center px-3.5 py-2.5 text-sm font-medium"
            style={{ color: "var(--series-blue)" }}
          >
            View all
          </button>
        </div>
      )}
    </div>
  );
}
