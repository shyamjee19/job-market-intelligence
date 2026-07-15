import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../api/authClient";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageTransition>
      <div className="max-w-sm mx-auto px-4 py-16">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Reset your password
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          We'll send a reset link to your email if an account exists.
        </p>

        <Card className="p-6">
          {sent ? (
            <div className="flex flex-col items-center gap-2 py-4 text-center">
              <CheckCircle2 size={24} style={{ color: "var(--status-good)" }} />
              <p className="text-sm" style={{ color: "var(--text-primary)" }}>
                If an account exists for <strong>{email}</strong>, a reset link is on its way.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <input
                type="email"
                required
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-primary)" }}
              />

              {error && (
                <div className="flex items-center gap-2 text-sm" style={{ color: "var(--status-critical)" }}>
                  <AlertTriangle size={14} />
                  {error}
                </div>
              )}

              <Button type="submit" variant="primary" disabled={loading} className="mt-1">
                {loading ? "Sending…" : "Send reset link"}
              </Button>
            </form>
          )}
        </Card>

        <p className="text-sm text-center mt-4" style={{ color: "var(--text-secondary)" }}>
          <Link to="/login" className="hover:underline" style={{ color: "var(--series-blue)" }}>
            Back to sign in
          </Link>
        </p>
      </div>
    </PageTransition>
  );
}
