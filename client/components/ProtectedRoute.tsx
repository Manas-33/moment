"use client";

import { ReactNode } from "react";

interface ProtectedRouteProps {
  children: ReactNode;
}

// Local mode: no auth — every route is accessible without a session.
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  return <>{children}</>;
}
