import * as React from "react";

import { cn } from "@/lib/utils";

export interface TelemetryPulseProps extends React.ComponentProps<"div"> {
  /** Mono caps status label, e.g. "ON TRACK", "SYNCING SESSION". */
  label?: string;
  /**
   * `sectors` (default): a row of sector segments lighting up in sequence.
   * `sweep`: a thin luminous bar sweeping a track line — for page-level loads.
   */
  variant?: "sectors" | "sweep";
}

const SEGMENTS = 5;

/**
 * The Pit Wall loading primitive. Telemetry treatments only — this design
 * system has no spinners and no three-dot typing indicators.
 */
export function TelemetryPulse({
  label,
  variant = "sectors",
  className,
  ...props
}: TelemetryPulseProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label ?? "Loading"}
      className={cn("flex items-center gap-3", className)}
      {...props}
    >
      {variant === "sectors" ? (
        <div className="flex items-center gap-1" aria-hidden>
          {Array.from({ length: SEGMENTS }, (_, i) => (
            <span
              key={i}
              className="h-1 w-5 rounded-full bg-race"
              style={{
                animation: "sector-cycle 1.4s ease-in-out infinite",
                animationDelay: `${i * 0.14}s`,
              }}
            />
          ))}
        </div>
      ) : (
        <div
          className="relative h-px w-40 overflow-hidden bg-line"
          aria-hidden
        >
          <span
            className="absolute inset-y-0 left-0 w-1/4 bg-gradient-to-r from-transparent via-race to-transparent"
            style={{ animation: "telemetry-sweep 1.2s linear infinite" }}
          />
        </div>
      )}
      {label && (
        <span className="text-data text-[10px] tracking-[0.25em] text-muted-foreground uppercase">
          {label}
        </span>
      )}
    </div>
  );
}

/** Full-screen centered pulse — used while the session is being resolved. */
export function TelemetryPulseScreen({ label }: { label?: string }) {
  return (
    <div className="flex min-h-svh items-center justify-center bg-background">
      <TelemetryPulse variant="sweep" label={label ?? "Syncing session"} />
    </div>
  );
}
