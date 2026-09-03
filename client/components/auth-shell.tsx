import Link from "next/link"

import { Logo } from "./logo"

const CLIP_HATCH: React.CSSProperties = {
  background:
    "repeating-linear-gradient(135deg,#2A2620,#2A2620 9px,#332F27 9px,#332F27 18px)",
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-svh bg-background">
      {/* brand panel */}
      <div className="relative hidden w-[45%] max-w-[600px] flex-none flex-col justify-between overflow-hidden bg-[#1E1B17] p-12 lg:flex">
        <div className="absolute -right-16 -top-20 h-72 w-72 rounded-full bg-primary/20 blur-3xl" />
        <Link href="/" className="relative flex items-center gap-3">
          <Logo size={34} />
          <span className="font-display text-xl font-bold tracking-tight text-[#F4F1EA]">Moment</span>
        </Link>
        <div className="relative">
          <h2 className="max-w-[420px] font-display text-[38px] font-bold leading-tight tracking-tight text-[#F4F1EA]">
            Short-form, on autopilot.
          </h2>
          <p className="mt-4 max-w-sm text-base leading-relaxed text-[#A39D8F]">
            Log in to turn any long video into a batch of captioned, ready-to-post vertical shorts.
          </p>
        </div>
        <div className="relative flex gap-3.5">
          {["clip", "this", "works"].map((w) => (
            <div
              key={w}
              className="flex aspect-[9/16] w-24 items-end justify-center rounded-xl border border-[#38332A] pb-3.5"
              style={CLIP_HATCH}
            >
              <span className="rounded bg-primary px-1.5 py-0.5 text-[11px] font-bold text-primary-foreground">{w}</span>
            </div>
          ))}
        </div>
      </div>

      {/* content */}
      <div className="flex flex-1 items-center justify-center p-6 sm:p-12">
        <div className="flex w-full max-w-sm flex-col">{children}</div>
      </div>
    </div>
  )
}
