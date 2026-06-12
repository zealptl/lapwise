import {
  SectorDivider,
  StintBlock,
  Surface,
  TelemetryPulse,
  TimingRow,
  Wordmark,
} from "@/components/telemetry";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { signOut } from "@/lib/auth/session";

/**
 * STUB — protected chat shell placeholder. Demonstrates the Pit Wall
 * composition later changes build on: timing-tower sidebar (conversation
 * history), full-width stint blocks (no bubbles), telemetry loading, and a
 * composer strip. The web-chat change replaces the demo content with the
 * live agent conversation.
 */
export default function ChatShellPage() {
  return (
    <div className="flex h-svh bg-background">
      {/* ── Timing tower (conversation sidebar placeholder) ───────────── */}
      <aside className="hidden w-72 shrink-0 flex-col border-r border-line bg-carbon-1 md:flex">
        <div className="flex items-center justify-between px-4 py-4">
          <Wordmark />
          <span className="text-data text-[10px] tracking-[0.2em] text-race uppercase">
            Stub
          </span>
        </div>
        <SectorDivider label="Sessions" className="px-2" />

        <nav className="mt-1 flex-1 overflow-y-auto" aria-label="Conversations">
          <TimingRow position={1} label="New session" value="--:--" active />
          <TimingRow position={2} label="Monaco strategy" value="14:02" />
          <TimingRow position={3} label="Value picks R8" value="TUE" />
          <TimingRow position={4} label="Risk-tolerant team" value="MON" />
        </nav>

        <div className="border-t border-line p-3">
          <Button
            variant="ghost"
            className="text-data w-full justify-between text-xs tracking-[0.15em] uppercase"
            onClick={() => signOut()}
          >
            Box box — sign out
            <span aria-hidden className="text-race">
              ▸
            </span>
          </Button>
        </div>
      </aside>

      {/* ── Race feed (chat placeholder) ──────────────────────────────── */}
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-line px-6 py-3">
          <h1 className="text-display text-lg tracking-wide">
            Pit wall <span className="text-muted-foreground">/ chat shell</span>
          </h1>
          <span className="text-data text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
            Foundation build
          </span>
        </header>

        <div className="mx-auto w-full max-w-3xl flex-1 space-y-5 overflow-y-auto px-6 py-8">
          <StintBlock role="user" timestamp="14:02:11" noLeadingLine>
            <p>
              Placeholder stint — your prompts render as full-width blocks,
              never bubbles. The web-chat change wires this feed to
              LapwiseF1Agent.
            </p>
          </StintBlock>

          <StintBlock role="agent" timestamp="14:02:33">
            <p>
              Agent stints carry the red LAPWISE marker and a sector line
              above. Markdown responses (best team / value picks /
              risk-tolerant scenarios) land here.
            </p>
          </StintBlock>

          <SectorDivider className="mt-8" />
          <TelemetryPulse label="Agent on track — demo of the loading state" />
        </div>

        {/* ── Composer strip (placeholder) ─────────────────────────────── */}
        <footer className="border-t border-line px-6 py-4">
          <Surface
            level={2}
            rail
            className="mx-auto flex w-full max-w-3xl items-center gap-3 p-2"
          >
            <Input
              placeholder="Radio check — composer lands in the web-chat change"
              className="border-0 bg-transparent shadow-none focus-visible:ring-0 dark:bg-transparent"
              disabled
            />
            <Button disabled className="text-display tracking-wider">
              Send
            </Button>
          </Surface>
        </footer>
      </main>
    </div>
  );
}
