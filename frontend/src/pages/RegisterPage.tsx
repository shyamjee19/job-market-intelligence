import { AlertTriangle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password, fullName || undefined);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
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
          Create an account
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Free - save jobs, follow companies, get alerts.
        </p>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <input
              type="text"
              placeholder="Full name (optional)"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
              style={inputStyle}
            />
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
              minLength={8}
              placeholder="Password (min. 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
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
              {loading ? "Creating account…" : "Create account"}
            </Button>
          </form>
        </Card>

        <p className="text-sm text-center mt-4" style={{ color: "var(--text-secondary)" }}>
          Already have an account?{" "}
          <Link to="/login" className="hover:underline" style={{ color: "var(--series-blue)" }}>
            Sign in
          </Link>
        </p>
      </div>
    </PageTransition>
  );
}
