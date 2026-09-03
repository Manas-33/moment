import Link from "next/link"
import {
  ArrowRight,
  Captions,
  Check,
  CheckCircle2,
  ChevronsDown,
  Languages,
  MonitorPlay,
  PlayCircle,
  Sparkles,
} from "lucide-react"

import { Logo } from "./logo"
import { Button } from "./ui/button"

const HATCH: React.CSSProperties = {
  background:
    "repeating-linear-gradient(135deg,#28251F,#28251F 11px,#312D26 11px,#312D26 22px)",
}

function LandingNav({ active }: { active?: "features" | "pricing" }) {
  return (
    <nav className="flex items-center justify-between border-b px-6 py-5 sm:px-14">
      <Link href="/" className="flex items-center gap-3">
        <Logo size={32} />
        <span className="font-display text-xl font-bold tracking-tight text-foreground">Moment</span>
      </Link>
      <div className="hidden items-center gap-8 text-sm font-medium text-sidebar-foreground md:flex">
        <a href="#how-it-works" className="text-sidebar-foreground hover:text-foreground">How it works</a>
        <a href="#features" className="text-sidebar-foreground hover:text-foreground">Features</a>
        <Link href="/pricing" className={active === "pricing" ? "font-semibold text-foreground" : "text-sidebar-foreground hover:text-foreground"}>Pricing</Link>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" asChild>
          <Link href="/login">Log in</Link>
        </Button>
        <Button asChild>
          <Link href="/dashboard">
            Get started
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </nav>
  )
}

function ClipMock({ time, word }: { time: string; word: string }) {
  return (
    <div
      className="relative flex aspect-[9/16] items-end justify-center overflow-hidden rounded-xl border pb-3.5 shadow-[0_8px_20px_-14px_rgba(30,27,23,0.3)]"
      style={HATCH}
    >
      <span className="absolute left-2 top-2 rounded bg-black/55 px-1.5 py-0.5 font-mono text-[10px] text-white">{time}</span>
      <span className="rounded bg-primary px-2 py-0.5 text-xs font-bold text-primary-foreground">{word}</span>
    </div>
  )
}

function Hero() {
  return (
    <section className="grid items-center gap-14 px-6 py-16 sm:px-14 lg:grid-cols-[1.02fr_0.98fr] lg:py-20">
      <div>
        <span className="label-mono text-xs text-primary">Video &rarr; shorts</span>
        <h1 className="mt-4 font-display text-[42px] font-extrabold leading-[1.03] tracking-tight text-foreground text-balance sm:text-[56px]">
          Turn any long video into shorts that get watched.
        </h1>
        <p className="mt-5 max-w-md text-lg leading-relaxed text-muted-foreground">
          Drop a YouTube link or upload a file. Moment finds your best moments, reframes them to
          9:16, and burns in captions, automatically.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-3.5">
          <Button size="lg" className="h-12 rounded-xl px-7 text-base" asChild>
            <Link href="/dashboard">
              Get started
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="h-12 rounded-xl px-6 text-base" asChild>
            <a href="#how-it-works">
              <PlayCircle className="h-[19px] w-[19px] text-primary" />
              Watch demo
            </a>
          </Button>
        </div>
        <div className="mt-6 flex items-center gap-2 text-[13px] font-medium text-muted-foreground">
          <CheckCircle2 className="h-4 w-4 text-primary" />
          No card required &middot; 5 free clips to start
        </div>
      </div>

      <div>
        <div
          className="relative flex aspect-video items-center justify-center overflow-hidden rounded-2xl border shadow-[0_24px_50px_-28px_rgba(30,27,23,0.4)]"
          style={HATCH}
        >
          <span className="absolute left-3.5 top-3.5 font-mono text-[11px] uppercase tracking-wide text-white/40">your video &middot; 58:24</span>
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/95 shadow-[0_8px_24px_-6px_rgba(0,0,0,0.5)]">
            <PlayCircle className="h-8 w-8 text-primary" />
          </div>
        </div>
        <div className="flex items-center justify-center gap-2.5 py-3.5">
          <span className="label-mono inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1.5 text-[11px] tracking-wider text-primary">Reframe &middot; caption</span>
          <ChevronsDown className="h-4 w-4 text-muted-foreground" />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <ClipMock time="0:38" word="changed" />
          <ClipMock time="0:52" word="about" />
          <ClipMock time="0:33" word="habit" />
        </div>
      </div>
    </section>
  )
}

function Logos() {
  return (
    <div className="px-6 pb-14 sm:px-14">
      <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 border-t pt-9">
        <span className="label-mono text-xs text-muted-foreground">Loved by creators at</span>
        {["[LOGO]", "[LOGO]", "[LOGO]", "[LOGO]", "[LOGO]"].map((l, i) => (
          <span key={i} className="font-mono text-[15px] font-semibold text-muted-foreground/60">{l}</span>
        ))}
      </div>
    </div>
  )
}

const STEPS = [
  { n: "01", title: "Transcribe", desc: "Accurate, word-level transcript in minutes." },
  { n: "02", title: "Pick moments", desc: "AI ranks the most clip-worthy 30–60s." },
  { n: "03", title: "Reframe to 9:16", desc: "Auto-crop that follows the active speaker." },
  { n: "04", title: "Caption", desc: "Word-level captions, highlighted as spoken." },
  { n: "05 · optional", title: "Dub", desc: "Translate and voice clips into new languages." },
]

function HowItWorks() {
  return (
    <section id="how-it-works" className="border-y bg-card px-6 py-16 sm:px-14">
      <div className="mx-auto max-w-6xl">
        <div className="mb-11">
          <span className="label-mono text-xs text-primary">How it works</span>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            From full video to five shorts
          </h2>
        </div>
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-5 lg:gap-0">
          {STEPS.map((s, i) => (
            <div key={s.title} className={`flex flex-col gap-2.5 px-0 lg:px-6 ${i > 0 ? "lg:border-l" : ""}`}>
              <div className="font-mono text-xs text-primary">{s.n}</div>
              <div className="text-base font-semibold text-foreground">{s.title}</div>
              <div className="text-[13px] leading-relaxed text-muted-foreground">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const FEATURES = [
  { icon: Captions, title: "Word-level captions", desc: "Highlights each word as it is spoken." },
  { icon: Sparkles, title: "AI moment detection", desc: "Finds hooks, punchlines, and payoffs." },
  { icon: Languages, title: "Multi-language dubbing", desc: "Translated, voiced clips for new audiences." },
  { icon: MonitorPlay, title: "1080p & 4K export", desc: "Crisp, platform-ready, no watermark." },
]

function FeaturesShowcase() {
  return (
    <section id="features" className="px-6 py-20 sm:px-14">
      <div className="mx-auto max-w-6xl">
        <div className="mb-11 text-center">
          <span className="label-mono text-xs text-primary">Features</span>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Built for the whole clip workflow
          </h2>
        </div>

        <div className="grid items-center gap-11 rounded-3xl border bg-card p-8 shadow-[0_16px_40px_-28px_rgba(30,27,23,0.2)] sm:p-10 lg:grid-cols-2">
          <div>
            <span className="label-mono text-xs text-primary">Speaker-aware reframing</span>
            <h3 className="mt-3.5 font-display text-2xl font-bold tracking-tight text-foreground">
              The crop follows whoever is talking.
            </h3>
            <p className="mt-3.5 text-[15px] leading-relaxed text-muted-foreground">
              No manual keyframing. Moment tracks the active speaker and keeps them centered in a
              clean vertical frame, even across cuts and multi-cam setups.
            </p>
            <div className="mt-5 flex flex-col gap-3">
              {["Multi-speaker tracking", "Smooth, broadcast-style motion"].map((t) => (
                <div key={t} className="flex items-center gap-2.5 text-sm font-medium text-foreground/80">
                  <Check className="h-[15px] w-[15px] text-primary" strokeWidth={2.5} />
                  {t}
                </div>
              ))}
            </div>
          </div>
          <div className="relative aspect-[16/10] overflow-hidden rounded-2xl" style={HATCH}>
            <div className="absolute left-[34%] top-[26%] h-14 w-14 rounded-full bg-white/15" />
            <div className="absolute bottom-[11%] left-[27%] top-[11%] w-[27%] rounded-lg border-2 border-dashed border-primary shadow-[0_0_0_100vmax_rgba(20,18,14,0.35)]" />
            <span className="label-mono absolute right-3.5 top-3.5 rounded-md bg-primary/20 px-2.5 py-1 text-[10px] tracking-wider text-primary">9:16 &middot; follows speaker</span>
          </div>
        </div>

        <div className="mt-9 grid gap-8 sm:grid-cols-2 lg:grid-cols-4 lg:gap-0">
          {FEATURES.map((f, i) => (
            <div key={f.title} className={`flex flex-col gap-2.5 px-0 lg:px-6 ${i > 0 ? "lg:border-l" : ""}`}>
              <f.icon className="h-[22px] w-[22px] text-primary" />
              <div className="text-[15px] font-semibold text-foreground">{f.title}</div>
              <div className="text-[13px] leading-relaxed text-muted-foreground">{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTA() {
  return (
    <section className="px-6 pb-20 sm:px-14">
      <div className="flex flex-col items-start justify-between gap-8 rounded-3xl bg-[#1E1B17] px-8 py-14 sm:px-14 md:flex-row md:items-center">
        <div>
          <h2 className="max-w-md font-display text-3xl font-bold leading-tight tracking-tight text-[#F4F1EA] sm:text-4xl">
            Ready to make your first short?
          </h2>
          <p className="mt-3.5 text-base text-[#A39D8F]">Your first five clips are on us. No card required.</p>
        </div>
        <Button size="lg" className="h-12 flex-none rounded-xl px-8 text-base" asChild>
          <Link href="/dashboard">
            Get started
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </section>
  )
}

function LandingFooter() {
  return (
    <footer className="flex flex-col items-center justify-between gap-4 border-t bg-card px-6 py-10 sm:flex-row sm:px-14">
      <div className="flex items-center gap-3">
        <Logo size={30} />
        <span className="font-display text-[17px] font-bold text-foreground">Moment</span>
        <span className="ml-2 text-[13px] text-muted-foreground">&copy; 2026 Moment Labs</span>
      </div>
      <div className="flex items-center gap-7 text-sm font-medium text-sidebar-foreground">
        <a href="#features" className="text-sidebar-foreground hover:text-foreground">Product</a>
        <Link href="/pricing" className="text-sidebar-foreground hover:text-foreground">Pricing</Link>
        <a href="#" className="text-sidebar-foreground hover:text-foreground">Docs</a>
        <a href="#" className="text-sidebar-foreground hover:text-foreground">Privacy</a>
      </div>
    </footer>
  )
}

export function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNav />
      <Hero />
      <Logos />
      <HowItWorks />
      <FeaturesShowcase />
      <CTA />
      <LandingFooter />
    </div>
  )
}

export { LandingNav, LandingFooter }
