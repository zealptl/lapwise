# web-foundation

## ADDED Requirements

### Requirement: SPA scaffold and local development
The system SHALL provide a React + Vite + TypeScript single-page application in `web/` that runs locally via `npm run dev` and builds via `npm run build` with zero TypeScript errors.

#### Scenario: Local development server
- **WHEN** a developer runs `npm install && npm run dev` in `web/`
- **THEN** the app serves at `http://localhost:5173` with hot module reload

#### Scenario: Production build passes
- **WHEN** `npm run build` is run
- **THEN** the build completes with no TypeScript or bundler errors

### Requirement: Environment configuration
The app SHALL read all AWS-specific values (Cognito user pool id, app client id, AgentCore runtime ARN, region, Lapwise API base URL) from Vite environment variables (`.env.local`), with a committed `.env.example` documenting every variable. No AWS identifiers SHALL be hardcoded in source.

#### Scenario: Missing configuration surfaces clearly
- **WHEN** the app starts without a required environment variable
- **THEN** it renders a clear configuration error naming the missing variable instead of failing opaquely at first API call

### Requirement: Auth-aware routing shell
The app SHALL use client-side routing with public routes (`/signin`, `/signup`, `/verify`) and a protected chat route (`/`). Unauthenticated access to a protected route SHALL redirect to `/signin`; authenticated access to `/signin` or `/signup` SHALL redirect to `/`.

#### Scenario: Unauthenticated user is redirected
- **WHEN** a user with no valid Cognito session navigates to `/`
- **THEN** they are redirected to `/signin`

#### Scenario: Authenticated user skips auth pages
- **WHEN** a user with a valid Cognito session navigates to `/signin`
- **THEN** they are redirected to `/`

### Requirement: F1 telemetry design system
The app SHALL implement a cohesive dark, motorsport-telemetry-inspired design system using Tailwind and shadcn/ui: layered carbon/near-black surfaces, a single racing accent color, condensed display typography paired with monospace data type, and purposeful motion. The implementation MUST be produced using the `frontend-design:frontend-design` skill, and generic AI-chat visual tropes (default chat bubbles, generic spinners, three-dot typing indicators, stock gradients on white) SHALL NOT be used.

#### Scenario: Consistent theming across all pages
- **WHEN** any page (signin, signup, verify, chat) renders
- **THEN** it uses the shared design tokens (colors, typography, spacing, motion) with no unstyled or default-shadcn-styled regions

#### Scenario: Distinctive loading states
- **WHEN** any asynchronous operation is in flight
- **THEN** the UI shows a telemetry-styled progress treatment rather than a generic spinner or typing dots
