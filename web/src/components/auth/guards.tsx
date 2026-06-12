import { Navigate, Outlet } from "react-router-dom";

import { TelemetryPulseScreen } from "@/components/telemetry";
import { useSession } from "@/lib/auth/use-session";

/**
 * Route guard for protected routes: unauthenticated visitors are
 * redirected to `/signin`. Shows a telemetry sweep while the session
 * resolves (never a spinner).
 */
export function RequireAuth() {
  const { loading, session } = useSession();

  if (loading) return <TelemetryPulseScreen label="Syncing session" />;
  if (!session) return <Navigate to="/signin" replace />;
  return <Outlet />;
}

/**
 * Route guard for public auth pages (`/signin`, `/signup`, `/verify`):
 * already-authenticated users are sent back to the pit wall at `/`.
 */
export function PublicOnly() {
  const { loading, session } = useSession();

  if (loading) return <TelemetryPulseScreen label="Syncing session" />;
  if (session) return <Navigate to="/" replace />;
  return <Outlet />;
}
