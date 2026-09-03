// Base URL of the Django backend API.
//
// Configure NEXT_PUBLIC_API_URL in the deployment environment (e.g. Vercel) to
// point at the deployed backend. Falls back to localhost for local development,
// so `npm run dev` against a local server keeps working with no env set.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
