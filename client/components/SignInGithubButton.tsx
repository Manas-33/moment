"use client"

import { Github } from "lucide-react"

import { Button } from "./ui/button"
import { signInWithGithub } from "@/lib/auth-action"

const SignInWithGithubButton = () => {
    return (
        <Button type="button" variant="outline" className="w-full" onClick={() => signInWithGithub()}>
            <Github className="mr-2 h-4 w-4" />
            Login with GitHub
        </Button>
    )
}

export default SignInWithGithubButton
