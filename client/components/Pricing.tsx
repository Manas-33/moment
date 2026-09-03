"use client"

import * as React from "react"
import Link from "next/link"
import { Check, Droplet } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "./ui/button"

type Feature = { label: string; muted?: boolean }

const PLANS = [
  {
    name: "Free",
    price: { monthly: "$0", yearly: "$0" },
    period: "/forever",
    tagline: "For trying Moment out.",
    cta: "Get started",
    href: "/dashboard",
    variant: "outline" as const,
    tone: "light" as const,
    features: [
      { label: "5 clips / month" },
      { label: "720p export" },
      { label: "Word-level captions" },
      { label: "Moment watermark", muted: true },
    ] as Feature[],
  },
  {
    name: "Pro",
    price: { monthly: "$29", yearly: "$23" },
    period: "/mo",
    tagline: "For creators publishing weekly.",
    cta: "Start Pro",
    href: "/dashboard",
    variant: "default" as const,
    tone: "featured" as const,
    features: [
      { label: "50 clips / month" },
      { label: "1080p export" },
      { label: "No watermark" },
      { label: "Batch processing" },
      { label: "Priority support" },
    ] as Feature[],
  },
  {
    name: "Enterprise",
    price: { monthly: "$99", yearly: "$79" },
    period: "/mo",
    tagline: "For teams and platforms at scale.",
    cta: "Contact sales",
    href: "mailto:sales@moment.com?subject=Enterprise%20Plan%20Inquiry",
    variant: "default" as const,
    tone: "dark" as const,
    features: [
      { label: "Unlimited clips" },
      { label: "4K export" },
      { label: "API access" },
      { label: "Team tools & roles" },
      { label: "Priority support" },
    ] as Feature[],
  },
]

export default function Pricing() {
  const [cycle, setCycle] = React.useState<"monthly" | "yearly">("monthly")

  return (
    <section id="pricing" className="px-6 py-20 sm:px-14">
      <div className="mx-auto flex max-w-[1120px] flex-col items-center text-center">
        <span className="label-mono text-xs text-primary">Pricing</span>
        <h1 className="mt-3 font-display text-4xl font-extrabold tracking-tight text-foreground sm:text-[44px]">
          Simple pricing that scales with you
        </h1>
        <p className="mt-4 max-w-lg text-[17px] leading-relaxed text-muted-foreground">
          Start free. Upgrade when you&apos;re ready to publish more. Cancel anytime.
        </p>

        <div className="mt-7 inline-flex gap-1 rounded-xl bg-muted p-1">
          <button
            onClick={() => setCycle("monthly")}
            className={cn(
              "rounded-lg px-5 py-2 text-[13px] font-semibold transition-colors",
              cycle === "monthly" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground",
            )}
          >
            Monthly
          </button>
          <button
            onClick={() => setCycle("yearly")}
            className={cn(
              "rounded-lg px-4 py-2 text-[13px] font-semibold transition-colors",
              cycle === "yearly" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground",
            )}
          >
            Yearly <span className="text-primary">&minus;20%</span>
          </button>
        </div>
      </div>

      <div className="mx-auto mt-11 grid max-w-[1120px] items-start gap-5 lg:grid-cols-3">
        {PLANS.map((plan) => {
          const dark = plan.tone === "dark"
          const featured = plan.tone === "featured"
          return (
            <div
              key={plan.name}
              className={cn(
                "relative flex flex-col gap-6 rounded-3xl p-8",
                dark
                  ? "bg-[#1E1B17] text-[#E7E3DA]"
                  : "border bg-card",
                featured && "border-2 border-primary shadow-[0_24px_50px_-26px_hsl(var(--primary)/0.45)]",
              )}
            >
              {featured && (
                <span className="label-mono absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-primary px-3.5 py-1.5 text-[11px] tracking-wider text-primary-foreground">
                  Most popular
                </span>
              )}

              <div>
                <div
                  className={cn(
                    "text-[15px] font-semibold",
                    featured ? "text-primary" : dark ? "text-[#FF8A63]" : "text-foreground",
                  )}
                >
                  {plan.name}
                </div>
                <div className="mt-4 flex items-baseline gap-1.5">
                  <span className={cn("font-display text-[46px] font-extrabold tracking-tight", dark ? "text-[#F4F1EA]" : "text-foreground")}>
                    {plan.price[cycle]}
                  </span>
                  {plan.name !== "Free" && (
                    <span className={cn("text-[15px] font-medium", dark ? "text-[#8F897C]" : "text-muted-foreground")}>
                      {plan.period}
                    </span>
                  )}
                  {plan.name === "Free" && (
                    <span className={cn("text-[15px] font-medium", dark ? "text-[#8F897C]" : "text-muted-foreground")}>
                      {plan.period}
                    </span>
                  )}
                </div>
                <div className={cn("mt-2 text-sm", dark ? "text-[#A39D8F]" : "text-muted-foreground")}>{plan.tagline}</div>
              </div>

              {dark ? (
                <Button asChild className="h-12 w-full rounded-xl bg-[#2E2A21] text-[#F4F1EA] hover:bg-[#38332A]">
                  <a href={plan.href}>{plan.cta}</a>
                </Button>
              ) : (
                <Button asChild variant={plan.variant} className="h-12 w-full rounded-xl">
                  <Link href={plan.href}>{plan.cta}</Link>
                </Button>
              )}

              <div className="flex flex-col gap-3.5">
                {plan.features.map((f) => (
                  <div
                    key={f.label}
                    className={cn(
                      "flex items-center gap-3 text-sm",
                      f.muted
                        ? dark ? "text-[#8F897C]" : "text-muted-foreground"
                        : dark ? "text-[#E7E3DA]" : "text-foreground/85",
                    )}
                  >
                    {f.muted ? (
                      <Droplet className="h-[15px] w-[15px] text-muted-foreground/60" />
                    ) : (
                      <Check className={cn("h-[15px] w-[15px]", dark ? "text-[#FF8A63]" : "text-primary")} strokeWidth={2.5} />
                    )}
                    {f.label}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      <p className="mt-10 text-center text-sm text-muted-foreground">
        All plans include word-level captions and 9:16 speaker-aware reframing.
      </p>
    </section>
  )
}
