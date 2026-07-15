import { AlertTriangle } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { oauthAuthorizeUrl } from "../api/authClient";
import { PageTransition } from "../components/PageTransition";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";
import type { RegisterPayload } from "../types";

const inputStyle = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  color: "var(--text-primary)",
};

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirmPassword: "",
    country: "",
    jobTitle: "",
    termsAccepted: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (!form.termsAccepted) {
      setError("You must accept the terms of service to create an account");
      return;
    }

    setLoading(true);
    try {
      const payload: RegisterPayload = {
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        confirm_password: form.confirmPassword,
        country: form.country || undefined,
        job_title: form.jobTitle || undefined,
        terms_accepted: form.termsAccepted,
      };
      await register(payload);
      // Auto-login on success - straight to the dashboard, never back to login.
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageTransition>
      <div className="max-w-md mx-auto px-4 py-16">
        <h1 className="text-2xl font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
          Create your account
        </h1>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
          Free — save jobs, follow companies, and unlock the AI tools.
        </p>

        <Card className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div className="grid grid-cols-2 gap-3">
              <input
                required
                placeholder="First name"
                value={form.firstName}
                onChange={(e) => update("firstName", e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />
              <input
                required
                placeholder="Last name"
                value={form.lastName}
                onChange={(e) => update("lastName", e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />
            </div>
            <input
              type="email"
              required
              placeholder="Email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
              style={inputStyle}
            />
            <input
              type="password"
              required
              minLength={8}
              placeholder="Password (min. 8 characters)"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
              style={inputStyle}
            />
            <input
              type="password"
              required
              minLength={8}
              placeholder="Confirm password"
              value={form.confirmPassword}
              onChange={(e) => update("confirmPassword", e.target.value)}
              className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
              style={inputStyle}
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                placeholder="Country (optional)"
                value={form.country}
                onChange={(e) => update("country", e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />
              <input
                placeholder="Role / title (optional)"
                value={form.jobTitle}
                onChange={(e) => update("jobTitle", e.target.value)}
                className="rounded-lg px-3.5 py-2.5 text-sm outline-none"
                style={inputStyle}
              />
            </div>

            <label className="flex items-start gap-2 text-xs mt-1" style={{ color: "var(--text-secondary)" }}>
              <input
                type="checkbox"
                checked={form.termsAccepted}
                onChange={(e) => update("termsAccepted", e.target.checked)}
                className="mt-0.5"
              />
              I agree to the Terms of Service and Privacy Policy.
            </label>

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

          <div className="flex items-center gap-3 my-4">
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
              or
            </span>
            <div className="flex-1 h-px" style={{ background: "var(--border)" }} />
          </div>

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
          Already have an account?{" "}
          <Link to="/login" className="hover:underline" style={{ color: "var(--series-blue)" }}>
            Sign in
          </Link>
        </p>
      </div>
    </PageTransition>
  );
}
