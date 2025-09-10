---
Title: ADR 0005: Adopt Next.js Over Vite for Frontend
Status: Accepted
Date: 2024-09-10
---

## Context

The original plan specified React 18 + Vite + TypeScript + Tailwind CSS on port 3001 for the frontend. However, the current implementation uses Next.js 14.2.5 with the app directory, Carbon UI components, and Sass on port 3000, providing server-side rendering (SSR) and improved developer experience (DX).

## Decision

Adopt Next.js 14.2.5 as the frontend framework, retaining the app directory structure and Carbon UI for styling. Align the port to 3000. Bridge the authentication mismatch where the backend uses JWT and the frontend uses OIDC via Next-Auth by extracting the JWT in the Next-Auth callback.

No migration to Vite is needed; proceed with the existing Next.js setup.

## Consequences

- **Positive:**

  - Leverages Next.js features like app router and static site generation (SSG) for faster prototyping and better SEO.
  - Improved DX with built-in optimizations and easier integration for full-stack features.

- **Negative:**
  - Team must learn Next.js specifics, such as the app directory and server components, which differ from Vite's setup.
  - Potential for framework lock-in compared to a lighter Vite build.

### Authentication Bridge Example

In `src/lib/auth.ts` (Next-Auth configuration), implement the JWT extraction in the callback:

```typescript
async jwt({ token, account }) {
  if (account) {
    // Extract backend JWT from OIDC access_token (assuming it contains the JWT)
    token.backendJWT = await extractJWT(account.access_token); // Implement extractJWT utility
  }
  return token;
}
```

This ensures compatibility between OIDC frontend auth and JWT backend expectations without major refactoring.
