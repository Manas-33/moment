import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { signup } from "@/lib/auth-action"
import SignInWithGoogleButton from "./SignInGoogleButton"
import SignInWithGithubButton from "./SignInGithubButton"

export function SignUpForm() {
  return (
    <>
      <h1 className="font-display text-3xl font-bold tracking-tight text-foreground">Create your account</h1>
      <p className="mt-2 text-[15px] text-muted-foreground">
        Your first five clips are on us. No card required.
      </p>

      <form className="mt-8 flex flex-col">
        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col">
            <Label htmlFor="first-name" className="mb-2 text-[13px] font-semibold text-foreground">First name</Label>
            <Input id="first-name" name="first-name" placeholder="Max" className="h-11 rounded-xl" required />
          </div>
          <div className="flex flex-col">
            <Label htmlFor="last-name" className="mb-2 text-[13px] font-semibold text-foreground">Last name</Label>
            <Input id="last-name" name="last-name" placeholder="Robinson" className="h-11 rounded-xl" required />
          </div>
        </div>

        <Label htmlFor="email" className="mb-2 mt-5 text-[13px] font-semibold text-foreground">Email</Label>
        <Input id="email" name="email" type="email" placeholder="you@studio.com" className="h-11 rounded-xl" required />

        <Label htmlFor="password" className="mb-2 mt-5 text-[13px] font-semibold text-foreground">Password</Label>
        <Input id="password" name="password" type="password" placeholder="••••••••" className="h-11 rounded-xl" required />

        <Button formAction={signup} type="submit" className="mt-6 h-12 rounded-xl text-[15px]">
          Create account
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
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-primary hover:underline">
          Log in
        </Link>
      </p>
    </>
  )
}
