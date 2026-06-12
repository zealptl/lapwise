import { useEffect, useState } from "react";

import {
  getCurrentSession,
  onSessionChange,
  type Session,
} from "@/lib/auth/session";

export interface SessionState {
  /** True until the initial `getCurrentSession()` resolves. */
  loading: boolean;
  session: Session | null;
}

/**
 * Resolve and track the current auth session. Re-renders on
 * sign-in/sign-out via `onSessionChange`.
 */
export function useSession(): SessionState {
  const [state, setState] = useState<SessionState>({
    loading: true,
    session: null,
  });

  useEffect(() => {
    let cancelled = false;

    getCurrentSession().then((session) => {
      if (!cancelled) setState({ loading: false, session });
    });

    const unsubscribe = onSessionChange((session) => {
      setState({ loading: false, session });
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  return state;
}
