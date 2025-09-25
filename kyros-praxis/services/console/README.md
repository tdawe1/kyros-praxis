# Kyros Console Service

The Kyros Console is a Next.js-based frontend application that provides the user interface for the Kyros Praxis AI orchestration platform. It features a modern React-based dashboard with real-time capabilities and comprehensive agent management.

## 🏗️ Architecture

### Technology Stack
- **Next.js 14** with App Router
- **React 18** with TypeScript
- **Carbon Design System** (IBM) for UI components
- **TanStack Query** for server state management
- **Zustand** for client state management
- **NextAuth v5** for authentication
- **Tailwind CSS** for styling

### Key Features
- **Dashboard Overview**: Real-time system monitoring and metrics
- **Agent Management**: Create, configure, and monitor AI agents
- **Job Monitoring**: Track job execution and results
- **Terminal Interface**: WebSocket-based terminal operations
- **Authentication**: Secure user authentication and authorization
- **Real-time Updates**: Live updates via WebSocket connections

## 🚀 Development Setup

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Access to orchestrator service (http://localhost:8000)
- Access to terminal daemon (ws://localhost:8787)

### Installation

1. **Clone and navigate to service**:
   ```bash
   cd services/console
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Environment Configuration**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with required variables:
   ```bash
   NEXTAUTH_URL=http://localhost:3001
   NEXTAUTH_SECRET=your_secure_secret_minimum_32_chars
   NEXT_PUBLIC_ADK_URL=http://localhost:8000
   KYROS_DAEMON_PORT=8787
   PORT=3001
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

The application will be available at http://localhost:3001

## 📁 Project Structure

```
services/console/
├── app/                    # Next.js App Router pages
│   ├── (dashboard)/       # Dashboard layout and pages
│   ├── api/              # API routes
│   ├── auth/             # Authentication pages
│   ├── agents/           # Agent management
│   └── jobs/             # Job monitoring
├── components/            # Reusable React components
├── lib/                  # Utility libraries and configs
├── hooks/                # Custom React hooks
├── types/                # TypeScript type definitions
└── public/               # Static assets
```

## 🔧 Development Commands

```bash
npm run dev          # Start development server with hot reload
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
npm test             # Run test suite
```

## 🔐 Authentication

The console uses NextAuth v5 for authentication with the following providers:

- **Credentials Provider**: Email/password authentication
- **OAuth Providers**: Google, GitHub (configurable)

### Authentication Flow
1. User submits credentials via login form
2. NextAuth validates against orchestrator API
3. JWT token issued and stored in HttpOnly cookies
4. Protected routes validate token on access
5. Automatic token refresh (when implemented)

## 🌐 API Integration

### Orchestrator API
- Base URL: `NEXT_PUBLIC_ADK_URL` (default: http://localhost:8000)
- Authentication: JWT tokens via NextAuth
- Key endpoints:
  - `POST /auth/login` - User authentication
  - `GET /api/v1/jobs` - List jobs
  - `POST /api/v1/jobs` - Create jobs
  - `GET /api/v1/collab/state/tasks` - List tasks

### WebSocket Connections
- **Terminal Daemon**: `ws://localhost:8787`
- **Real-time Updates**: Connection to orchestrator WebSocket endpoint

## 🎨 UI Components

### Carbon Design System
The console uses IBM's Carbon Design System for consistent, accessible UI components:

- **Primary Components**: Buttons, Modals, Forms, Tables
- **Layout Components**: Grid, Stack, Shell
- **Feedback Components**: Toasts, Notifications, Loading states

### Custom Components
- **Dashboard**: Metrics overview and system health
- **Agent Cards**: Agent status and capabilities display
- **Job Timeline**: Visual job execution tracking
- **Terminal**: Real-time terminal interface

## 📊 State Management

### Server State (TanStack Query)
```typescript
// Fetching jobs
const { data: jobs, isLoading } = useQuery({
  queryKey: ['jobs'],
  queryFn: () => fetch('/api/v1/jobs').then(res => res.json())
});
```

### Client State (Zustand)
```typescript
// Dashboard store
import { create } from 'zustand';

const useDashboardStore = create((set) => ({
  selectedAgent: null,
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
}));
```

## 🔄 Real-time Features

### WebSocket Terminal
- Secure WebSocket connection to terminal daemon
- Real-time command execution and output streaming
- Session management and persistence
- Multiple terminal support

### Live Updates
- Job status updates via WebSocket
- Real-time metrics and monitoring
- Push notifications for important events

## 🧪 Testing

### Unit Tests
```bash
npm run test:unit    # Run unit tests with Jest
```

### Integration Tests
```bash
npm run test:integration  # Run integration tests with Playwright
```

### E2E Tests
```bash
npm run test:e2e     # Run end-to-end tests
```

## 🚀 Deployment

### Environment Variables
Required environment variables for production:

```bash
# Application
NEXTAUTH_URL=https://your-domain.com
PORT=3001

# Security
NEXTAUTH_SECRET=your_production_secret
NODE_ENV=production

# API URLs
NEXT_PUBLIC_ADK_URL=https://api.your-domain.com
KYROS_DAEMON_PORT=8787
```

### Build and Deploy
```bash
npm run build       # Create production build
npm run start       # Start production server
```

### Docker Deployment
```dockerfile
# Using provided Dockerfile
docker build -t kyros-console .
docker run -p 3001:3001 kyros-console
```

## 🔧 Troubleshooting

### Common Issues

**Build Errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

**Port Already in Use**
```bash
# Kill process on port 3001
lsof -ti:3001 | xargs kill -9
```

**Authentication Issues**
1. Verify `NEXTAUTH_SECRET` is set correctly
2. Check orchestrator API is accessible
3. Verify CORS settings on orchestrator
4. Check browser console for errors

**WebSocket Connection Issues**
1. Verify terminal daemon is running
2. Check firewall/network settings
3. Verify WebSocket URL configuration
4. Check browser WebSocket support

### Debug Mode
Enable debug logging for development:

```bash
DEBUG=* npm run dev
```

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Carbon Design System](https://carbondesignsystem.com/)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [NextAuth Documentation](https://next-auth.js.org/)
- [Overall Project Documentation](../../docs/)
- [API Documentation](../../docs/api/README.md)