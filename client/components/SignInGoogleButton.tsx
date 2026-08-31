"use client"

import { Button } from "./ui/button"
import { signInWithGoogle } from "@/lib/auth-action"

const SignInWithGoogleButton = () => {
    return (
        <Button type="button" variant="outline" className="w-full" onClick={() => signInWithGoogle()}>
            Login with Google
        </Button>
    )
}

export default SignInWithGoogleButton