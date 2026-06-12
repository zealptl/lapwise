import { SectorDivider, Surface, Wordmark } from "@/components/telemetry";

/**
 * Full-screen configuration failure — rendered by the root config gate when
 * required `VITE_*` variables are missing. Styled as a red-flag board.
 */
export function ConfigError({ missing }: { missing: string[] }) {
  return (
    <div className="flex min-h-svh items-center justify-center bg-background p-6">
      <Surface level={1} className="w-full max-w-xl overflow-hidden">
        <div className="flex items-center justify-between bg-race px-5 py-2">
          <span className="text-display text-sm tracking-[0.25em] text-primary-foreground">
            Red flag — configuration
          </span>
          <span className="text-data text-[10px] text-primary-foreground/80">
            ENV
          </span>
        </div>

        <div className="space-y-5 p-6">
          <Wordmark />
          <p className="text-sm text-muted-foreground">
            The app cannot start: required environment variables are missing.
            Copy <code className="text-data text-foreground">.env.example</code>{" "}
            to <code className="text-data text-foreground">.env</code> in{" "}
            <code className="text-data text-foreground">web/</code> and restart
            the dev server.
          </p>

          <SectorDivider label={`${missing.length} missing`} />

          <ul className="space-y-2">
            {missing.map((name) => (
              <li
                key={name}
                className="flex items-center gap-3 border border-line bg-carbon-2 px-3 py-2"
              >
                <span aria-hidden className="h-3 w-0.5 shrink-0 bg-race" />
                <span className="text-data text-sm text-foreground">
                  {name}
                </span>
                <span className="text-data ml-auto text-[10px] tracking-[0.2em] text-race uppercase">
                  Not set
                </span>
              </li>
            ))}
          </ul>
        </div>
      </Surface>
    </div>
  );
}
