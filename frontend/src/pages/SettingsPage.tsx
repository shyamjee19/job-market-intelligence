import { AlertTriangle, KeyRound, Link2, Mail, Shield, UserCircle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { changePassword } from "../api/authClient";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";
import { formatDate } from "../lib/format";

const inputStyle = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  color: "var(--text-primary)",
};

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleChangePassword(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("New passwords do not match");
      return;
    }

    setSaving(true);
    try {
      await changePassword(currentPassword, newPassword);
      // Changing password revokes every session server-side - the local
      // one included, so sign out here rather than pretend it's still valid.
      await logout();
      navigate("/login", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update password");
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageTransition>
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-semibold mb-6" style={{ color: "var(--text-primary)" }}>
          Settings
        </h1>

        <div className="flex flex-col gap-6">
          <Card className="p-6">
            <h2 className="flex items-center gap-2 text-sm font-semibold mb-4" style={{ color: "var(--text-secondary)" }}>
              <UserCircle size={15} />
              Account
            </h2>
            <div className="flex flex-col gap-3 text-sm">
              <div className="flex items-center gap-2.5" style={{ color: "var(--text-primary)" }}>
                <Mail size={14} style={{ color: "var(--text-muted)" }} />
                {user?.email}
              </div>
              <div className="flex items-center gap-2.5" style={{ color: "var(--text-primary)" }}>
                <Shield size={14} style={{ color: "var(--text-muted)" }} />
                {user?.role === "admin" ? "Administrator" : "Member"} · joined {user ? formatDate(user.created_at) : "—"}
              </div>
              <div className="flex items-center gap-2.5" style={{ color: "var(--text-secondary)" }}>
                <Link2 size={14} style={{ color: "var(--text-muted)" }} />
                Connect Google/GitHub from the login page to sign in with them next time.
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="flex items-center gap-2 text-sm font-semibold mb-4" style={{ color: "var(--text-secondary)" }}>
              <KeyRound size={15} />
              Change password
            </h2>
            <form onSubmit={handleChangePassword} className="flex flex-col gap-3">
              <input
                type="password"
                required
                placeholder="Current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />
              <input
                type="password"
                required
                minLength={8}
                placeholder="New password (min. 8 characters)"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />
              <input
                type="password"
                required
                minLength={8}
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />

              {error && (
                <div className="flex items-center gap-2 text-sm" style={{ color: "var(--status-critical)" }}>
                  <AlertTriangle size={14} />
                  {error}
                </div>
              )}

              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Changing your password signs you out of every device, including this one.
              </p>

              <Button type="submit" variant="primary" disabled={saving} className="mt-1 self-start">
                {saving ? "Updating…" : "Update password"}
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </PageTransition>
  );
}
