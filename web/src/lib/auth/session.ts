/**
 * Lapwise session module — INTERFACE CONTRACT.
 *
 * ⚠️ STUB: every function below currently behaves as "no user signed in".
 * The web-auth change implements these against `amazon-cognito-identity-js`
 * (CognitoUserPool / CognitoUser, SRP auth flow) WITHOUT changing any
 * signature — the router guards, the chat shell, and the API clients all
 * consume this module and must not need edits when real auth lands.
 *
 * Implementation notes for the web-auth agent:
 * - Pool/client ids come from `getConfig()` in `@/lib/config`
 *   (`cognitoUserPoolId`, `cognitoClientId`).
 * - `amazon-cognito-identity-js` caches tokens in localStorage and
 *   `CognitoUser.getSession` transparently refreshes with the refresh token;
 *   `getCurrentSession` should wrap `userPool.getCurrentUser()?.getSession()`.
 * - Token routing (per design.md): the **ID token** authorizes AgentCore
 *   `InvokeAgentRuntime` (audience check), the **access token** authorizes
 *   the Lapwise HTTP API. Hence the two separate getters.
 * - `onSessionChange` lets the router re-evaluate guards after
 *   sign-in/sign-out without a full reload; fire it from the auth pages'
 *   success paths and from `signOut`.
 */

/** Decoded identity of the signed-in Cognito user. */
export interface SessionUser {
  /** Cognito `sub` claim — used as `user_id` / `actor_id` everywhere. */
  sub: string;
  /** Verified email address. */
  email: string;
}

/** An authenticated Cognito session with valid (non-expired) tokens. */
export interface Session {
  user: SessionUser;
  /** Raw JWT for AgentCore InvokeAgentRuntime (`aud` = app client id). */
  idToken: string;
  /** Raw JWT for the Lapwise HTTP API (JWT authorizer). */
  accessToken: string;
  /** Epoch milliseconds at which the id/access tokens expire. */
  expiresAt: number;
}

type SessionListener = (session: Session | null) => void;
const listeners = new Set<SessionListener>();

/**
 * Resolve the current session, refreshing tokens if needed.
 * Resolves `null` when no user is signed in or refresh fails.
 */
export async function getCurrentSession(): Promise<Session | null> {
  // STUB — web-auth implements via CognitoUserPool.getCurrentUser().
  return null;
}

/**
 * Convenience getter: a fresh **ID token**, or `null` if signed out.
 * Use for `Authorization: Bearer` on AgentCore invocations.
 */
export async function getIdToken(): Promise<string | null> {
  const session = await getCurrentSession();
  return session?.idToken ?? null;
}

/**
 * Convenience getter: a fresh **access token**, or `null` if signed out.
 * Use for `Authorization: Bearer` on the Lapwise HTTP API.
 */
export async function getAccessToken(): Promise<string | null> {
  const session = await getCurrentSession();
  return session?.accessToken ?? null;
}

/**
 * Sign the current user out (clear cached Cognito tokens) and notify
 * listeners. Safe to call when already signed out.
 */
export function signOut(): void {
  // STUB — web-auth implements via CognitoUser.signOut().
  notifySessionChange(null);
}

/**
 * Subscribe to session changes (sign-in, sign-out, expiry). Returns an
 * unsubscribe function. The router guards use this to re-run redirects.
 */
export function onSessionChange(listener: SessionListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/**
 * Notify subscribers that the session changed. The web-auth implementation
 * calls this after successful sign-in/confirmation and on sign-out.
 */
export function notifySessionChange(session: Session | null): void {
  for (const listener of listeners) listener(session);
}
