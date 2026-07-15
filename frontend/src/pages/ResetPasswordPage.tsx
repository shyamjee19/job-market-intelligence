import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { resetPassword } from "../api/authClient";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (!token) {
      setError("This reset link is missing its token");
      return;
    }

    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "This reset link is invalid or has expired");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle = {
    background: "var(--surface-1)",
    border: "1px solid var(--border)",
    color: "var(--text-primary)",
  };

  return (
    <PageTransition>
      <div className="max-w-sm mx-auto px-4 py-16">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Set a new password
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Choose a new password for your account.
        </p>

        <Card className="p-6">
          {done ? (
            <div className="flex flex-col items-center gap-3 py-4 text-center">
              <CheckCircle2 size={24} style={{ color: "var(--status-good)" }} />
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                Your password has been updated. Please sign in again.
              </p>
              <Link to="/login">
                <Button variant="primary">Sign in</Button>
              </Link>
            </div>
          ) : !token ? (
            <div className="flex items-center gap-2 text-sm" style={{ color: "var(--status-critical)" }}>
              <AlertTriangle size={14} />
              This reset link is missing its token. Request a new one from the forgot-password page.
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                type="password"
                required
                minLength={8}
                placeholder="New password (min. 8 characters)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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

              <Button type="submit" variant="primary" disabled={loading} className="mt-1">
                {loading ? "Updating…" : "Update password"}
              </Button>
            </form>
          )}
        </Card>
      </div>
    </PageTransition>
  );
}
