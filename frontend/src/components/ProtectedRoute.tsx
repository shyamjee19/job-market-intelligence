import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function AdminRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== "admin") return <Navigate to="/" replace />;
  return <>{children}</>;
}

/** For /login, /register, /forgot-password - an already-authenticated
 * visitor skips straight to the dashboard rather than seeing a login form. */
export function GuestOnlyRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (user) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}
