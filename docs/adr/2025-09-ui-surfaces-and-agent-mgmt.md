# ADR: UI Surfaces and Agent Management

**Date**: 2025-09-13  
**Status**: Accepted  
**Deciders**: Frontend Tech Lead  

## Context

Kyros Praxis requires a comprehensive frontend UI to manage multiple business surfaces including agent management, translations, quotes, inventory, marketing, remote access, personal assistant, and system settings. The primary focus is on delivering a high-polish Agent Management feature while scaffolding the remaining modules with functional placeholders.

## Decision

We will build a Next.js 14 App Router-based frontend using:
- **Carbon Design System** for consistent UI components
- **TanStack Query** for server state management
- **React Hook Form + Zod** for form handling and validation
- **MSW** for API mocking during development
- **next-intl** for internationalization support

### Information Architecture

```
/(dashboard)
  /agents          - Agent Management (primary focus)
  /translations    - Content translation workflows
  /quotes          - Quote generation and management
  /inventory       - Product catalog and stock
  /marketing       - Analytics and campaign management
  /remote          - Remote terminal access
  /assistant       - Personal AI assistant
  /settings        - Organization and system settings
  /system          - Infrastructure monitoring
```

### Component Architecture

1. **Layout Structure**
   - Persistent Carbon Header with global navigation
   - Collapsible SideNav with route groups
   - Breadcrumb navigation for context
   - Error boundaries at route group level

2. **State Management**
   - TanStack Query for server state with optimistic updates
   - Zustand for client-only state (UI preferences, drafts)
   - URL state for filters, pagination, and view settings
   - localStorage for user preferences and draft forms

3. **Data Layer**
   - OpenAPI TypeScript client generation (when available)
   - MSW for development and testing mocks
   - Consistent query key patterns: `['resource', 'action', ...params]`
   - Exponential backoff retry strategy (except 4xx errors)

4. **Form Strategy**
   - React Hook Form for all forms
   - Zod schemas for validation and type safety
   - Multi-step wizards with localStorage draft persistence
   - Optimistic updates with rollback on error

5. **Authentication & Authorization**
   - JWT-based authentication (existing)
   - RBAC with viewer/editor/admin roles
   - Server-side auth guards via middleware
   - Client-side permission checks for UI elements

## Agent Management Deep Dive

### Core Features

1. **Agent List**
   - Carbon DataTable with virtual scrolling for large datasets
   - Advanced filtering (status, capabilities, owner)
   - Bulk operations (pause, resume, delete)
   - Persistent table state in URL params

2. **Agent Create/Edit Wizard**
   - Multi-step form: Basics → Capabilities → Policies → Connectors → Scheduling → Review
   - Form draft auto-save to localStorage
   - JSON diff preview before save
   - Reusable for both create and edit flows

3. **Agent Detail Views**
   - Overview: status, health metrics, recent runs
   - Playground: interactive chat with streaming logs
   - Runs: execution history with detailed logs
   - Secrets: secure credential management
   - Evaluations: test suite results and metrics

4. **Real-time Features**
   - WebSocket connection for live logs
   - SSE for status updates
   - Optimistic UI updates with rollback

### Data Models

```typescript
// Core schemas
interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'paused' | 'error';
  model: string;
  temperature: number;
  maxTokens: number;
  capabilities: Capability[];
  policies: Policy[];
  connectors: Connector[];
  schedule?: Schedule;
  owner: string;
  createdAt: Date;
  updatedAt: Date;
}

interface Capability {
  id: string;
  name: string;
  type: 'function' | 'tool' | 'knowledge';
  config: Record<string, any>;
  dependencies: string[];
}

interface Policy {
  id: string;
  type: 'domain' | 'pii' | 'safety' | 'custom';
  rules: Rule[];
  enabled: boolean;
}
```

## Other Surfaces (Scaffolded)

Each surface will have:
- Basic CRUD operations with Carbon DataTable
- Empty states with clear CTAs
- Form validation with Zod
- Loading skeletons and error boundaries
- Feature flags for gradual rollout

## Accessibility & Performance

- **WCAG 2.1 AA** compliance target
- Focus management for keyboard navigation
- ARIA labels and live regions for screen readers
- Code splitting at route group level
- Image optimization with next/image
- Static generation where possible

## Testing Strategy

1. **Unit Tests** (Vitest + React Testing Library)
   - Component rendering and interactions
   - Hook behavior
   - Zod schema validation

2. **Integration Tests** (MSW)
   - API interaction flows
   - Form submission workflows
   - Error handling scenarios

3. **E2E Tests** (Playwright)
   - Critical user journeys (Agent CRUD)
   - Cross-browser compatibility
   - Visual regression testing

## Security Considerations

- CSP headers configured in next.config.js
- XSS prevention via React's built-in escaping
- CSRF protection via double-submit cookies
- Secure credential storage (never in localStorage)
- Input sanitization on all user inputs

## Migration Path

1. Preserve existing pages during migration
2. Feature flag new surfaces
3. Gradual rollout with A/B testing capability
4. Maintain backward compatibility with existing APIs

## Consequences

### Positive
- Consistent UI/UX across all surfaces
- Type-safe development with TypeScript + Zod
- Excellent developer experience with hot reload and mocking
- Accessible by default with Carbon Design System
- Performance optimized with Next.js App Router

### Negative
- Initial learning curve for Carbon Design System
- Bundle size increase from comprehensive component library
- Complexity of managing multiple state systems
- Need for comprehensive test coverage

### Risks & Mitigations
- **Risk**: API endpoints not ready
  - **Mitigation**: MSW mocks with realistic data
- **Risk**: Performance issues with large datasets
  - **Mitigation**: Virtual scrolling, pagination, lazy loading
- **Risk**: Browser compatibility issues
  - **Mitigation**: Progressive enhancement, polyfills where needed

## References

- [Carbon Design System](https://carbondesignsystem.com/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [TanStack Query](https://tanstack.com/query)
- [React Hook Form](https://react-hook-form.com/)
- [MSW](https://mswjs.io/)

## Decision Record

- **2025-09-13**: Initial ADR created
- **2025-09-13**: Approved for implementation