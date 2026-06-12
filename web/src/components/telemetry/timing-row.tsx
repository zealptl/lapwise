import * as React from "react";

import { cn } from "@/lib/utils";

export interface TimingRowProps extends React.ComponentProps<"button"> {
  /** Position number, rendered timing-tower style (P1, P2, …). */
  position?: number;
  /** Primary label (conversation name, driver, …). */
  label: string;
  /** Trailing mono value — a timestamp, gap, or lap time. */
  value?: string;
  /** Highlight as the currently selected row (red rail + brighter text). */
  active?: boolean;
}

/**
 * Position-style row for the timing-tower sidebar: rank, label, mono value.
 * Renders as a button so rows are natively focusable/clickable.
 */
export function TimingRow({
  position,
  label,
  value,
  active = false,
  className,
  ...props
}: TimingRowProps) {
  return (
    <button
      type="button"
      data-active={active || undefined}
      className={cn(
        "group relative flex w-full items-center gap-3 border-b border-line px-3 py-2 text-left transition-colors",
        "hover:bg-carbon-2 focus-visible:bg-carbon-2 focus-visible:outline-none",
        active && "bg-carbon-2",
        className,
      )}
      {...props}
    >
      <span
        aria-hidden
        className={cn(
          "absolute inset-y-0 left-0 w-0.5 bg-race opacity-0 transition-opacity",
          active && "opacity-100",
        )}
      />
      {position !== undefined && (
        <span className="text-data w-7 shrink-0 text-xs text-muted-foreground">
          {String(position).padStart(2, "0")}
        </span>
      )}
      <span
        className={cn(
          "text-display flex-1 truncate text-sm tracking-wide",
          active ? "text-foreground" : "text-foreground/80",
        )}
      >
        {label}
      </span>
      {value && (
        <span className="text-data shrink-0 text-[11px] text-muted-foreground">
          {value}
        </span>
      )}
    </button>
  );
}
