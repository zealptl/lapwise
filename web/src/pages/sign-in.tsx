import { Link } from "react-router-dom";

import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * STUB — placeholder sign-in page. The web-auth change replaces the inert
 * form with a real Cognito SRP flow via `@/lib/auth/session`.
 */
export default function SignInPage() {
  return (
    <AuthLayout
      title="Sign in"
      subtitle="Authenticate to reach the pit wall. This page is a styled stub — Cognito sign-in lands in the web-auth change."
    >
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" placeholder="you@example.com" disabled />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" placeholder="••••••••" disabled />
        </div>
        <Button type="submit" className="w-full" disabled>
          Sign in — coming in web-auth
        </Button>
      </form>
      <p className="mt-4 text-center text-xs text-muted-foreground">
        No seat yet?{" "}
        <Link to="/signup" className="text-race hover:underline">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
