import Link from "next/link"

import { Logo } from "@/components/logo"
import { Button } from "@/components/ui/button"

export default function ErrorPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-background px-6 text-center">
      <Logo size={44} />
      <h1 className="mt-6 font-display text-3xl font-bold tracking-tight text-foreground">
        Something went wrong
      </h1>
      <p className="mt-3 max-w-sm text-[15px] leading-relaxed text-muted-foreground">
        We hit a snag loading this page. Try again, or head back to the studio to keep making
        shorts.
      </p>
      <div className="mt-7 flex items-center gap-3">
        <Button asChild>
          <Link href="/dashboard">Back to studio</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/">Go home</Link>
        </Button>
      </div>
    </div>
  )
}
