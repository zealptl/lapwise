# Lapwise Web — Pit Wall

Chat UI for the LapwiseF1Agent (Vite + React + TypeScript + Tailwind v4 +
shadcn/ui + React Router).

## Setup

```bash
cd web
npm install
cp .env.example .env   # public identifiers, see .env.example
npm run dev            # serves on http://localhost:5173 (pinned — CORS)
```

`npm run build` type-checks and bundles; `npm run lint` runs ESLint.

## Layout

- `src/lib/config.ts` — typed `import.meta.env` config; missing vars render
  a full-screen red-flag error.
- `src/lib/auth/session.ts` — session interface contract (currently a stub;
  implemented against `amazon-cognito-identity-js` by the web-auth change).
- `src/components/telemetry/` — the "Pit Wall" design primitives
  (`Surface`, `SectorDivider`, `TimingRow`, `TelemetryPulse`, `StintBlock`,
  `Wordmark`). See `src/components/telemetry/index.ts` for the rules of the
  design system.
- `src/pages/` — `/` chat shell (protected), `/signin`, `/signup`,
  `/verify` (public stubs). Guards live in `src/components/auth/guards.tsx`.
