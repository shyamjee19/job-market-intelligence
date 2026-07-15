import { Bell, CheckCheck, Inbox } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchNotifications, markAllNotificationsRead, markNotificationRead } from "../api/userClient";
import { PageTransition } from "../components/PageTransition";
import { Pagination } from "../components/Pagination";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { formatDate } from "../lib/format";
import type { Notification } from "../types";

const PAGE_SIZE = 20;

export function NotificationsPage() {
  const [items, setItems] = useState<Notification[] | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setItems(null);
    fetchNotifications(page, PAGE_SIZE)
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch(() => setItems([]));
  }, [page]);

  async function handleMarkRead(id: number) {
    setItems((prev) => prev?.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n)) ?? null);
    await markNotificationRead(id).catch(() => {});
  }

  async function handleMarkAllRead() {
    setItems((prev) => prev?.map((n) => ({ ...n, is_read: true })) ?? null);
    await markAllNotificationsRead().catch(() => {});
  }

  const hasUnread = items?.some((n) => !n.is_read) ?? false;

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="flex items-center gap-2 text-2xl font-semibold" style={{ color: "var(--text-primary)" }}>
            <Bell size={22} style={{ color: "var(--series-blue)" }} />
            Notifications
          </h1>
          {hasUnread && (
            <Button size="sm" onClick={handleMarkAllRead}>
              <CheckCheck size={14} />
              Mark all read
            </Button>
          )}
        </div>

        {items === null ? (
          <div className="space-y-2">
            <Skeleton className="h-16 w-full rounded-xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
          </div>
        ) : items.length === 0 ? (
          <Card className="flex flex-col items-center gap-2 py-16 text-center">
            <Inbox size={26} style={{ color: "var(--text-muted)" }} />
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              No notifications yet. Job alert matches will show up here.
            </p>
          </Card>
        ) : (
          <div className="flex flex-col gap-2">
            {items.map((n) => (
              <Card
                key={n.notification_id}
                className="p-4 cursor-pointer"
                onClick={() => !n.is_read && handleMarkRead(n.notification_id)}
                style={{
                  background: n.is_read ? "var(--surface-1)" : "color-mix(in srgb, var(--series-blue) 6%, var(--surface-1))",
                  border: n.is_read ? "1px solid var(--border)" : "1px solid color-mix(in srgb, var(--series-blue) 25%, var(--border))",
                }}
              >
                <div className="flex items-start gap-2.5">
                  {!n.is_read && <span className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0" style={{ background: "var(--series-blue)" }} />}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
                        {n.subject ?? "Notification"}
                      </p>
                      <span className="text-xs shrink-0" style={{ color: "var(--text-muted)" }}>
                        {formatDate(n.created_at)}
                      </span>
                    </div>
                    {n.body && (
                      <p className="text-sm mt-1 whitespace-pre-wrap" style={{ color: "var(--text-secondary)" }}>
                        {n.body}
                      </p>
                    )}
                    <span
                      className="inline-block mt-2 text-[11px] font-medium rounded-full px-2 py-0.5"
                      style={{
                        background: n.status === "sent" ? "color-mix(in srgb, var(--status-good) 14%, var(--surface-1))" : "var(--surface-2)",
                        color: n.status === "sent" ? "var(--status-good)" : "var(--text-muted)",
                      }}
                    >
                      {n.status === "sent" ? "Emailed" : "Logged"}
                    </span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {items !== null && items.length > 0 && <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />}
      </div>
    </PageTransition>
  );
}
