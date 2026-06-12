/**
 * Pit Wall design primitives — compose these (plus the themed shadcn
 * Button/Input/Label) for all Lapwise UI. Rules of the system:
 *
 * - Surfaces layer via the carbon ladder (Surface level 0–3), not shadows.
 * - One accent: racing red. Sector purple/green/yellow are status-only.
 * - Dividers are hairline luminous lines (SectorDivider).
 * - Conversation turns are full-width StintBlocks — never chat bubbles.
 * - Loading is TelemetryPulse — never spinners or three-dot indicators.
 * - Headings use `text-display` (condensed caps); data uses `text-data`.
 */
export { Surface } from "./surface";
export { SectorDivider } from "./sector-divider";
export { TimingRow } from "./timing-row";
export { TelemetryPulse, TelemetryPulseScreen } from "./telemetry-pulse";
export { StintBlock } from "./stint-block";
export { Wordmark } from "./wordmark";
