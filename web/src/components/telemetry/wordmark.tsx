import { cn } from "@/lib/utils";

/**
 * LAPWISE wordmark — condensed caps split by a racing-red slash, like a
 * timing-screen team tag.
 */
export function Wordmark({
  className,
  size = "md",
}: {
  className?: string;
  size?: "md" | "lg";
}) {
  return (
    <span
      className={cn(
        "text-display inline-flex items-baseline gap-1 leading-none font-bold",
        size === "lg" ? "text-4xl" : "text-xl",
        className,
      )}
    >
      <span>LAP</span>
      <span aria-hidden className="text-race italic">
        /
      </span>
      <span>WISE</span>
    </span>
  );
}
