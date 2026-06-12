import { Link } from "react-router-dom";

import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * STUB — placeholder email-verification page. The web-auth change wires
 * the Cognito confirmation-code flow here.
 */
export default function VerifyPage() {
  return (
    <AuthLayout
      title="Verify"
      subtitle="Enter the code sent to your email. This page is a styled stub — code confirmation lands in the web-auth change."
    >
      <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
        <div className="space-y-1.5">
          <Label htmlFor="code">Verification code</Label>
          <Input
            id="code"
            inputMode="numeric"
            placeholder="000000"
            className="text-data tracking-[0.5em]"
            disabled
          />
        </div>
        <Button type="submit" className="w-full" disabled>
          Verify — coming in web-auth
        </Button>
      </form>
      <p className="mt-4 text-center text-xs text-muted-foreground">
        Wrong inbox?{" "}
        <Link to="/signup" className="text-race hover:underline">
          Back to sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
