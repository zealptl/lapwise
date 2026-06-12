import type { ReactNode } from "react";

import { SectorDivider, Surface, Wordmark } from "@/components/telemetry";

/**
 * Shared frame for the public auth pages: wordmark over a single carbon
 * panel with a mono session header, like a pre-race formation screen.
 */
export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-8 bg-background p-6">
      <div className="grid-rise" style={{ animationDelay: "0ms" }}>
        <Wordmark size="lg" />
      </div>

      <Surface
        level={1}
        className="grid-rise w-full max-w-sm p-6"
        style={{ animationDelay: "90ms" }}
      >
        <div className="mb-1 flex items-baseline justify-between">
          <h1 className="text-display text-2xl tracking-wide">{title}</h1>
          <span className="text-data text-[10px] tracking-[0.2em] text-race uppercase">
            Stub
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
        <SectorDivider className="my-5" />
        {children}
      </Surface>

      <p
        className="text-data grid-rise text-[10px] tracking-[0.25em] text-muted-foreground/60 uppercase"
        style={{ animationDelay: "180ms" }}
      >
        F1 Fantasy strategy · Pit wall access
      </p>
    </div>
  );
}
