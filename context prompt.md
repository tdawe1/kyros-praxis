# Overview

This is a fullstack web application for managing and monitoring AI agent workflows called "Kyros". The system provides a dashboard interface for tracking runs, monitoring agents, managing terminal sessions, and viewing system health. It's built as a modern React frontend with an Express.js backend and uses Drizzle ORM for database operations.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: React with TypeScript using Vite for development and bundling
- **Routing**: Wouter for lightweight client-side routing
- **State Management**: TanStack Query (React Query) for server state management and caching
- **UI Components**: Radix UI primitives with shadcn/ui components and Tailwind CSS for styling
- **Form Handling**: React Hook Form with Zod validation
- **Build Tool**: Vite with custom configuration for development and production builds

## Backend Architecture
- **Framework**: Express.js with TypeScript
- **Database Layer**: Drizzle ORM with PostgreSQL dialect
- **Storage Pattern**: Interface-based storage with in-memory implementation (MemStorage) for development
- **API Design**: RESTful endpoints with structured error handling and request logging
- **Development Server**: Custom Vite integration for seamless full-stack development

## Database Schema
The application uses PostgreSQL with the following core entities:
- **Runs**: Workflow executions with status tracking, PR information, and agent assignments
- **Agents**: AI agents with different runners (SDK/CLI), models, and status management
- **System Health**: Service monitoring with health checks and status reporting
- **Users**: Basic user management (schema defined but not fully implemented)

## Key Design Patterns
- **Separation of Concerns**: Clear separation between client, server, and shared code
- **Type Safety**: Full TypeScript coverage with shared types between frontend and backend
- **Component Composition**: Modular React components with consistent design patterns
- **Query Optimization**: Automatic data refetching with configurable intervals for real-time updates
- **Error Boundaries**: Structured error handling with user-friendly error states

# External Dependencies

## Database
- **Neon Database**: Serverless PostgreSQL database (@neondatabase/serverless)
- **Drizzle ORM**: Type-safe database operations with migration support

## UI Framework
- **Radix UI**: Accessible component primitives for complex UI elements
- **Tailwind CSS**: Utility-first CSS framework with custom design system
- **Lucide React**: Icon library for consistent iconography

## Development Tools
- **Replit Integration**: Custom Vite plugins for Replit development environment
- **ESBuild**: Fast JavaScript bundling for production builds
- **PostCSS**: CSS processing with Tailwind and Autoprefixer

## Real-time Features
- **WebSocket Support**: Planned integration for terminal sessions (ws://localhost:8787/term)
- **Polling Strategy**: Configurable refetch intervals for dashboard updates and system monitoring

## Third-party Integrations
- **GitHub Integration**: Pull request information handling and repository management
- **Terminal Daemon**: WebSocket connection to external terminal service
- **Orchestrator Service**: HTTP API integration for system configuration and health checks