import type { PromptTemplate } from './types';

export const templates: PromptTemplate[] = [
  {
    id: 'web-application',
    name: 'Web Application',
    description: 'Full-stack web app with user accounts and admin tools.',
    prompt: 'I want to build a web application with...',
    sections: {
      purpose:
        'Build a responsive web application that helps project teams capture requirements, collaborate on delivery plans, and track status in real-time.',
      features: [
        '• User authentication with email + OAuth providers.',
        '• Role-based access (contributors, reviewers, admins).',
        '• Dashboard summarizing project milestones and blockers.',
        '• Commenting system on tasks with mentions and notifications.',
        '• Export project status reports as PDF or CSV.',
      ].join('\n'),
      techStack:
        'Frontend: React 18 + Next.js 15 with Tailwind CSS.\nAPI: Node.js with Fastify.\nDatabase: PostgreSQL 15 with Prisma ORM.\nHosting: Vercel frontend, Railway backend.',
    },
  },
  {
    id: 'rest-api',
    name: 'REST API',
    description: 'Backend service exposing RESTful endpoints.',
    prompt: 'I need a REST API that...',
    sections: {
      purpose:
        'Create a REST API that powers a mobile application for tracking personal fitness goals and workout sessions.',
      features: [
        '• CRUD endpoints for workouts, exercises, and progress snapshots.',
        '• JWT authentication with refresh token rotation.',
        '• Rate limiting per user to avoid abuse.',
        '• Aggregated analytics endpoint returning weekly summaries.',
        '• OpenAPI schema generation and Swagger UI for docs.',
      ].join('\n'),
      techStack:
        'Runtime: Python 3.12 with FastAPI.\nDatabase: PostgreSQL with SQLAlchemy ORM.\nQueue: Redis-based task queue for async processing.\nDeployment: Dockerized service deployed on Fly.io.',
    },
  },
  {
    id: 'cli-tool',
    name: 'CLI Tool',
    description: 'Command-line automation utility.',
    prompt: 'Create a CLI tool to...',
    sections: {
      purpose:
        'Develop a command-line interface that automates release note generation from Git commit history.',
      features: [
        '• Parse conventional commits and group by type.',
        '• Generate markdown output with hyperlinks to commits.',
        '• Provide interactive mode to curate notable changes.',
        '• Support configuration file for custom categories.',
        '• Offer dry-run mode and exit codes for CI integration.',
      ].join('\n'),
      techStack:
        'Language: TypeScript executed with ts-node.\nDependencies: commander.js for CLI, simple-git for git interactions.\nDistribution: Package via npm and provide single-file standalone build.',
    },
  },
];

