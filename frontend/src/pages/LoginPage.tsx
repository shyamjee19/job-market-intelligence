import { AlertTriangle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { oauthAuthorizeUrl } from "../api/authClient";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password, rememberMe);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
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
          Sign in
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Save jobs, follow companies, and set up alerts.
        </p>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input
              type="email"
              required
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
              style={inputStyle}
            />
            <input
              type="password"
              required
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
              style={inputStyle}
            />

            <div className="flex items-center justify-between text-xs" style={{ color: "var(--text-secondary)" }}>
              <label className="flex items-center gap-1.5">
                <input type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} />
                Remember me
              </label>
              <Link to="/forgot-password" className="hover:underline" style={{ color: "var(--series-blue)" }}>
                Forgot password?
              </Link>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-sm" style={{ color: "var(--status-critical)" }}>
                <AlertTriangle size={14} />
                {error}
              </div>
            )}

            <Button type="submit" variant="primary" disabled={loading} className="mt-1">
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              or
            </span>
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
          </div>

          {/* Redirects to the backend's OAuth flow - returns a clear error
              if Google/GitHub credentials aren't configured yet (see README). */}
          <div className="flex flex-col gap-2">
            <a href={oauthAuthorizeUrl("google")}>
              <Button className="w-full">Continue with Google</Button>
            </a>
            <a href={oauthAuthorizeUrl("github")}>
              <Button className="w-full">Continue with GitHub</Button>
            </a>
          </div>
        </Card>

        <p className="text-sm text-center mt-4" style={{ color: "var(--text-secondary)" }}>
          Don't have an account?{" "}
          <Link to="/register" className="hover:underline" style={{ color: "var(--series-blue)" }}>
            Create one
          </Link>
        </p>
      </div>
    </PageTransition>
  );
}
