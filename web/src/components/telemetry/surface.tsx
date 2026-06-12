import * as React from "react";

import { cn } from "@/lib/utils";

const LEVELS = {
  0: "bg-carbon-0",
  1: "bg-carbon-1",
  2: "bg-carbon-2",
  3: "bg-carbon-3",
} as const;

export interface SurfaceProps extends React.ComponentProps<"div"> {
  /** Carbon ladder elevation: 0 (page void) → 3 (highest). Default 1. */
  level?: keyof typeof LEVELS;
  /** Hairline border around the surface. Default true. */
  bordered?: boolean;
  /** 2px racing-red rail on the left edge (active / emphasized panels). */
  rail?: boolean;
}

/**
 * Layered carbon panel — the basic Pit Wall container. Compose levels to
 * create depth instead of using shadows.
 */
export function Surface({
  level = 1,
  bordered = true,
  rail = false,
  className,
  ...props
}: SurfaceProps) {
  return (
    <div
      data-slot="surface"
      className={cn(
        "relative rounded-md",
        LEVELS[level],
        bordered && "border border-line",
        rail &&
          "before:absolute before:inset-y-0 before:left-0 before:w-0.5 before:rounded-l-md before:bg-race",
        className,
      )}
      {...props}
    />
  );
}
