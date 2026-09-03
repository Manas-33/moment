"use client"

import { Github } from "lucide-react"

import { Button } from "./ui/button"
import { signInWithGithub } from "@/lib/auth-action"

const SignInWithGithubButton = () => {
  return (
    <Button
      type="button"
      variant="outline"
      className="h-11 w-full gap-2.5 rounded-xl text-sm font-semibold"
      onClick={() => signInWithGithub()}
    >
      <Github className="h-[18px] w-[18px]" />
      Continue with GitHub
    </Button>
  )
}

export default SignInWithGithubButton
