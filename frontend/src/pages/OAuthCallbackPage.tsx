import { AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { exchangeOAuthCode } from "../api/authClient";
import { PageTransition } from "../components/PageTransition";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

export function OAuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const { loginWithTokens } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("No authorization code was returned.");
      return;
    }

    exchangeOAuthCode(code)
      .then((tokens) => loginWithTokens(tokens.access_token, tokens.refresh_token))
      .then(() => {
        window.location.replace("/");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Sign-in failed"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <PageTransition>
      <div className="max-w-sm mx-auto px-4 py-16">
        <Card className="p-6 text-center">
          {error ? (
            <>
              <AlertTriangle size={24} className="mx-auto mb-2" style={{ color: "var(--status-critical)" }} />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                {error}
              </p>
              <Link to="/login" className="text-sm hover:underline mt-3 inline-block" style={{ color: "var(--series-blue)" }}>
                Back to sign in
              </Link>
            </>
          ) : (
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              Signing you in…
            </p>
          )}
        </Card>
      </div>
    </PageTransition>
  );
}
