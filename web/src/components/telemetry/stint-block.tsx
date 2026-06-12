import * as React from "react";

import { SectorDivider } from "@/components/telemetry/sector-divider";
import { cn } from "@/lib/utils";

export interface StintBlockProps extends React.ComponentProps<"section"> {
  /** Who produced this stint: the user or the Lapwise agent. */
  role: "user" | "agent";
  /** Mono timestamp shown in the stint header (e.g. "14:02:33"). */
  timestamp?: string;
  /** Hide the leading sector line (e.g. for the first block in a feed). */
  noLeadingLine?: boolean;
}

/**
 * Full-width conversation block — the Pit Wall alternative to chat bubbles.
 * Each turn is a "stint": a header strip (role marker + mono timestamp)
 * over full-width content, separated from the previous stint by a sector
 * line. Agent stints carry the racing-red marker.
 */
export function StintBlock({
  role,
  timestamp,
  noLeadingLine = false,
  className,
  children,
  ...props
}: StintBlockProps) {
  const isAgent = role === "agent";
  return (
    <section
      data-role={role}
      className={cn("w-full", className)}
      {...props}
    >
      {!noLeadingLine && <SectorDivider className="mb-5" />}
      <header className="mb-2 flex items-baseline gap-3">
        <span
          className={cn(
            "text-display text-xs tracking-[0.18em]",
            isAgent ? "text-race" : "text-muted-foreground",
          )}
        >
          {isAgent ? "LAPWISE" : "YOU"}
        </span>
        {timestamp && (
          <span className="text-data text-[10px] text-muted-foreground/70">
            {timestamp}
          </span>
        )}
      </header>
      <div className="text-[15px] leading-relaxed text-foreground/90">
        {children}
      </div>
    </section>
  );
}
