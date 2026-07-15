import { AlertTriangle, ScrollText, ShieldCheck, UserCheck, Users as UsersIcon, UserX } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchAdminStats, fetchAdminUsers, fetchAuditLogs, updateUserActive, updateUserRole } from "../api/adminClient";
import { PageTransition } from "../components/PageTransition";
import { Pagination } from "../components/Pagination";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";
import { formatDate } from "../lib/format";
import type { AdminStats, AdminUser, AuditLog } from "../types";

const PAGE_SIZE = 20;

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4">
      <div className="text-2xl font-semibold tabular" style={{ color: "var(--text-primary)" }}>
        {value.toLocaleString()}
      </div>
      <div className="text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
        {label}
      </div>
    </Card>
  );
}

function UsersTable() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchAdminUsers(page, PAGE_SIZE)
      .then((res) => {
        setUsers(res.items);
        setTotal(res.total);
      })
      .catch((err) => setError(err.message ?? "Failed to load users"))
      .finally(() => setLoading(false));
  }, [page]);

  async function handleRoleChange(u: AdminUser, role: "user" | "admin") {
    setUsers((prev) => prev.map((x) => (x.user_id === u.user_id ? { ...x, role } : x)));
    await updateUserRole(u.user_id, role).catch(() => {});
  }

  async function handleActiveToggle(u: AdminUser) {
    const next = !u.is_active;
    setUsers((prev) => prev.map((x) => (x.user_id === u.user_id ? { ...x, is_active: next } : x)));
    await updateUserActive(u.user_id, next).catch(() => {});
  }

  if (error) {
    return (
      <Card className="flex items-center gap-2 p-4" style={{ color: "var(--status-critical)" }}>
        <AlertTriangle size={16} />
        <span className="text-sm">{error}</span>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}>
              <th className="text-left font-medium px-4 py-2.5">User</th>
              <th className="text-left font-medium px-4 py-2.5">Role</th>
              <th className="text-left font-medium px-4 py-2.5">Status</th>
              <th className="text-left font-medium px-4 py-2.5">Joined</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
                  Loading…
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={u.user_id} style={{ borderTop: "1px solid var(--border)" }}>
                  <td className="px-4 py-3">
                    <div className="font-medium" style={{ color: "var(--text-primary)" }}>
                      {u.full_name || u.email}
                    </div>
                    <div className="text-xs" style={{ color: "var(--text-secondary)" }}>
                      {u.email}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={u.role}
                      disabled={u.user_id === me?.user_id}
                      onChange={(e) => handleRoleChange(u, e.target.value as "user" | "admin")}
                      className="rounded-lg text-xs px-2 py-1 outline-none"
                      style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className="rounded-full px-2 py-0.5 text-xs font-medium"
                      style={{
                        background: u.is_active
                          ? "color-mix(in srgb, var(--status-good) 14%, var(--surface-1))"
                          : "color-mix(in srgb, var(--status-critical) 14%, var(--surface-1))",
                        color: u.is_active ? "var(--status-good)" : "var(--status-critical)",
                      }}
                    >
                      {u.is_active ? "Active" : "Suspended"}
                    </span>
                  </td>
                  <td className="px-4 py-3 tabular" style={{ color: "var(--text-secondary)" }}>
                    {formatDate(u.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button size="sm" disabled={u.user_id === me?.user_id} onClick={() => handleActiveToggle(u)}>
                      {u.is_active ? <UserX size={13} /> : <UserCheck size={13} />}
                      {u.is_active ? "Suspend" : "Reactivate"}
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="px-4 pb-4">
        <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
      </div>
    </Card>
  );
}

function AuditLogTable() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchAuditLogs(page, PAGE_SIZE)
      .then((res) => {
        setLogs(res.items);
        setTotal(res.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page]);

  return (
    <Card className="overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "var(--surface-2)", color: "var(--text-secondary)" }}>
              <th className="text-left font-medium px-4 py-2.5">When</th>
              <th className="text-left font-medium px-4 py-2.5">User</th>
              <th className="text-left font-medium px-4 py-2.5">Action</th>
              <th className="text-left font-medium px-4 py-2.5">Resource</th>
              <th className="text-left font-medium px-4 py-2.5">IP</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
                  Loading…
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm" style={{ color: "var(--text-secondary)" }}>
                  No audit events yet.
                </td>
              </tr>
            ) : (
              logs.map((l) => (
                <tr key={l.log_id} style={{ borderTop: "1px solid var(--border)" }}>
                  <td className="px-4 py-3 tabular whitespace-nowrap" style={{ color: "var(--text-secondary)" }}>
                    {formatDate(l.created_at)}
                  </td>
                  <td className="px-4 py-3 tabular" style={{ color: "var(--text-secondary)" }}>
                    {l.user_id ?? "—"}
                  </td>
                  <td className="px-4 py-3 font-medium" style={{ color: "var(--text-primary)" }}>
                    {l.action}
                  </td>
                  <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>
                    {l.resource_type ? `${l.resource_type}${l.resource_id ? ` #${l.resource_id}` : ""}` : "—"}
                  </td>
                  <td className="px-4 py-3 tabular" style={{ color: "var(--text-secondary)" }}>
                    {l.ip_address ?? "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <div className="px-4 pb-4">
        <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
      </div>
    </Card>
  );
}

export function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    fetchAdminStats().then(setStats).catch(() => {});
  }, []);

  return (
    <PageTransition>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="flex items-center gap-2 text-2xl font-semibold mb-6" style={{ color: "var(--text-primary)" }}>
          <ShieldCheck size={22} style={{ color: "var(--series-blue)" }} />
          Admin dashboard
        </h1>

        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <StatTile label="Total users" value={stats.total_users} />
            <StatTile label="Admins" value={stats.admin_users} />
            <StatTile label="New today" value={stats.new_users_today} />
            <StatTile label="Active users" value={stats.active_users} />
          </div>
        )}

        <section className="mb-8">
          <h2 className="flex items-center gap-2 text-sm font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>
            <UsersIcon size={15} />
            Users
          </h2>
          <UsersTable />
        </section>

        <section>
          <h2 className="flex items-center gap-2 text-sm font-semibold mb-3" style={{ color: "var(--text-secondary)" }}>
            <ScrollText size={15} />
            Audit log
          </h2>
          <AuditLogTable />
        </section>
      </div>
    </PageTransition>
  );
}
