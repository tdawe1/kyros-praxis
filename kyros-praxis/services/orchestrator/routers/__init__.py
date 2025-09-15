"""
API Router Modules Package

This package contains all the RESTful API router modules for the Kyros Orchestrator service.
Each module is responsible for a specific domain or functionality area within the service.

Router Modules:
- escalation.py: Escalation system API endpoints for intelligent task escalation decisions
- events.py: Event management endpoints for logging and streaming system events
- jobs.py: Job management endpoints for creating, tracking, and managing jobs
- monitoring.py: Monitoring and observability endpoints for health checks and metrics
- orchestrator_events.py: Orchestrator-specific event streaming and retrieval endpoints
- security.py: Security monitoring and reporting endpoints for CSP violations and security checks
- tasks.py: Collaborative task management endpoints for shared work items
- utils.py: Utility endpoints for health checks and service information

The routers are designed to be modular and loosely coupled, allowing for independent development
and testing of each functional area while maintaining consistent API design principles
throughout the service.
"""
