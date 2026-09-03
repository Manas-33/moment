import { cn } from "@/lib/utils"

/**
 * Moment brand mark: a play triangle cut out of a soft accent tile.
 * Reads at 16px in the nav, works as a favicon, and drops onto a home
 * screen as an app icon.
 */
export function Logo({
  size = 34,
  className,
}: {
  size?: number
  className?: string
}) {
  return (
    <div
      className={cn(
        "flex flex-none items-center justify-center bg-primary text-primary-foreground shadow-[0_4px_12px_-3px_hsl(var(--primary)/0.55)]",
        className,
      )}
      style={{ width: size, height: size, borderRadius: Math.round(size * 0.29) }}
      aria-hidden
    >
      <svg
        width={Math.round(size * 0.44)}
        height={Math.round(size * 0.44)}
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M8 5.14v13.72a1 1 0 0 0 1.53.85l10.8-6.86a1 1 0 0 0 0-1.7L9.53 4.29A1 1 0 0 0 8 5.14Z" />
      </svg>
    </div>
  )
}
