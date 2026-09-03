import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { login } from "@/lib/auth-action"
import SignInWithGoogleButton from "./SignInGoogleButton"
import SignInWithGithubButton from "./SignInGithubButton"

export function LoginForm() {
  return (
    <>
      <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">Log in</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        Welcome back. Let&apos;s make some shorts.
      </p>

      <form className="mt-8 flex flex-col">
        <Label htmlFor="email" className="mb-2 text-[13px] font-semibold text-foreground">Email</Label>
        <Input
          id="email"
          name="email"
          type="email"
          placeholder="you@studio.com"
          className="h-11 rounded-xl"
          required
        />

        <div className="mb-2 mt-5 flex items-center justify-between">
          <Label htmlFor="password" className="text-[13px] font-semibold text-foreground">Password</Label>
          <a href="#" className="text-[13px] font-medium text-primary hover:underline">Forgot?</a>
        </div>
        <Input
          id="password"
          name="password"
          type="password"
          placeholder="••••••••"
          className="h-11 rounded-xl"
          required
        />

        <Button formAction={login} type="submit" className="mt-6 h-12 rounded-xl text-[15px]">
          Log in
        </Button>
      </form>

      <div className="my-6 flex items-center gap-3.5">
        <div className="h-px flex-1 bg-border" />
        <span className="label-mono text-xs text-muted-foreground">or</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <div className="flex flex-col gap-2.5">
        <SignInWithGoogleButton />
        <SignInWithGithubButton />
      </div>

      <p className="mt-7 text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-semibold text-primary hover:underline">
          Sign up
        </Link>
      </p>
    </>
  )
}
