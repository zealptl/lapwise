import * as React from "react";

import { cn } from "@/lib/utils";

export interface SectorDividerProps extends React.ComponentProps<"div"> {
  /**
   * Optional label rendered mid-line in mono caps, timing-screen style
   * (e.g. "LAP 12", a timestamp, or a role marker).
   */
  label?: string;
  /** Tint the line with the racing accent instead of neutral luminance. */
  accent?: boolean;
}

/**
 * Thin luminous divider evoking F1 timing screens. Separates stint blocks,
 * sidebar sections, and form regions.
 */
export function SectorDivider({
  label,
  accent = false,
  className,
  ...props
}: SectorDividerProps) {
  const line = (
    <div
      aria-hidden
      className={cn(
        "sector-line flex-1",
        accent &&
          "[background:linear-gradient(90deg,transparent,var(--race)_12%,var(--race)_88%,transparent)] opacity-70",
      )}
    />
  );

  if (!label) {
    return (
      <div
        role="separator"
        className={cn("flex items-center", className)}
        {...props}
      >
        {line}
      </div>
    );
  }

  return (
    <div
      role="separator"
      className={cn("flex items-center gap-3", className)}
      {...props}
    >
      {line}
      <span className="text-data shrink-0 text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
        {label}
      </span>
      {line}
    </div>
  );
}
