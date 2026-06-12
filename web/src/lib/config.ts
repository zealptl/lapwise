/**
 * Typed runtime configuration read from `import.meta.env`.
 *
 * Every value is required. Use {@link loadConfig} at the application root —
 * it returns the missing variable names instead of throwing so the app can
 * render a clear full-screen error (see `components/ConfigError`).
 *
 * `getConfig` is for modules that run strictly after the root config gate
 * (API clients, auth) and may safely assume configuration is present.
 */

export interface AppConfig {
  /** AWS region, e.g. `us-east-1`. */
  awsRegion: string;
  /** Cognito User Pool id, e.g. `us-east-1_Q1p1bedp6`. */
  cognitoUserPoolId: string;
  /** Cognito app client id (LapwiseAppClient). */
  cognitoClientId: string;
  /** BedrockAgentCore runtime ARN for LapwiseF1Agent. */
  agentRuntimeArn: string;
  /** Base URL of the Lapwise HTTP API (conversations endpoints). */
  lapwiseApiUrl: string;
}

const ENV_VARS: Record<keyof AppConfig, string> = {
  awsRegion: "VITE_AWS_REGION",
  cognitoUserPoolId: "VITE_COGNITO_USER_POOL_ID",
  cognitoClientId: "VITE_COGNITO_CLIENT_ID",
  agentRuntimeArn: "VITE_AGENT_RUNTIME_ARN",
  lapwiseApiUrl: "VITE_LAPWISE_API_URL",
};

export type ConfigResult =
  | { ok: true; config: AppConfig }
  | { ok: false; missing: string[] };

export function loadConfig(): ConfigResult {
  const env = import.meta.env as Record<string, string | undefined>;
  const missing: string[] = [];
  const config = {} as AppConfig;

  for (const [key, envName] of Object.entries(ENV_VARS) as [
    keyof AppConfig,
    string,
  ][]) {
    const value = env[envName]?.trim();
    if (!value) {
      missing.push(envName);
    } else {
      config[key] = value;
    }
  }

  return missing.length > 0 ? { ok: false, missing } : { ok: true, config };
}

let cached: AppConfig | null = null;

/**
 * Returns the validated config. Throws if configuration is incomplete —
 * only call from code that runs behind the root config gate.
 */
export function getConfig(): AppConfig {
  if (cached) return cached;
  const result = loadConfig();
  if (!result.ok) {
    throw new Error(
      `Missing required environment variables: ${result.missing.join(", ")}`,
    );
  }
  cached = result.config;
  return cached;
}
