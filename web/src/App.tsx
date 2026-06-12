import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { PublicOnly, RequireAuth } from "@/components/auth/guards";
import { ConfigError } from "@/components/config-error";
import { loadConfig } from "@/lib/config";
import ChatShellPage from "@/pages/chat-shell";
import SignInPage from "@/pages/sign-in";
import SignUpPage from "@/pages/sign-up";
import VerifyPage from "@/pages/verify";

const router = createBrowserRouter([
  {
    element: <RequireAuth />,
    children: [{ path: "/", element: <ChatShellPage /> }],
  },
  {
    element: <PublicOnly />,
    children: [
      { path: "/signin", element: <SignInPage /> },
      { path: "/signup", element: <SignUpPage /> },
      { path: "/verify", element: <VerifyPage /> },
    ],
  },
]);

export default function App() {
  // Config gate: refuse to boot the router without complete configuration.
  const config = loadConfig();
  if (!config.ok) {
    return <ConfigError missing={config.missing} />;
  }

  return <RouterProvider router={router} />;
}
