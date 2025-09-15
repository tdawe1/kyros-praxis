# Kyros Hybrid Model System - API Documentation

## Table of Contents
- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Task Management API](#task-management-api)
- [Agent Coordination API](#agent-coordination-api)
- [Model Selection API](#model-selection-api)
- [Escalation API](#escalation-api)
- [Monitoring API](#monitoring-api)
- [Configuration API](#configuration-api)
- [Webhooks](#webhooks)
- [WebSocket API](#websocket-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Integration Examples](#integration-examples)

## API Overview

### Base URL
- **Production**: `https://api.kyros.com/v1`
- **Staging**: `https://staging-api.kyros.com/v1`
- **Development**: `http://localhost:8000/v1`

### API Versioning
All API requests are versioned using the `/v1/` prefix. Future versions will be `/v2/`, `/v3/`, etc.

### Response Format
All API responses follow this standard format:

```json
{
  "success": true,
  "data": {},
  "message": "Success message",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested resource was not found",
    "details": {}
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Content Types
- **Requests**: `application/json`
- **Responses**: `application/json`
- **File Uploads**: `multipart/form-data`

## Authentication

### JWT Authentication
Most API endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### OAuth2 Integration
Kyros supports OAuth2 for authentication:

**Endpoints:**
```
GET  /auth/oauth2/{provider}
POST /auth/oauth2/{provider}/callback
POST /auth/token
POST /auth/refresh
```

**OAuth2 Providers Supported:**
- Google
- GitHub
- Microsoft
- Custom OAuth2 providers

### API Key Authentication
For service-to-service authentication:

```http
X-API-Key: your-api-key-here
```

### Authentication Endpoints

#### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=your_username&password=your_password
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "roles": ["developer", "admin"]
    }
  }
}
```

#### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### User Profile
```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "roles": ["developer", "admin"],
    "permissions": ["create_task", "review_code"],
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
  }
}
```

## Task Management API

### Create Task
```http
POST /tasks
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "title": "Implement user authentication",
  "description": "Add JWT-based authentication system with OAuth2 integration",
  "type": "implementation",
  "priority": "high",
  "assignee_role": "implementer",
  "files_to_modify": [
    "services/orchestrator/auth.py",
    "services/console/src/auth/index.ts"
  ],
  "acceptance_criteria": [
    "Users can register with email/password",
    "OAuth2 integration works with Google",
    "JWT tokens are properly validated",
    "Refresh token mechanism implemented"
  ],
  "dependencies": [],
  "tags": ["authentication", "security", "backend"],
  "deadline": "2024-01-20T23:59:59Z",
  "metadata": {
    "estimated_hours": 8,
    "complexity": "medium"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task_123456",
    "title": "Implement user authentication",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "created_by": "user_123",
    "assignee_role": "implementer",
    "priority": "high",
    "estimated_hours": 8,
    "deadline": "2024-01-20T23:59:59Z"
  }
}
```

### Get Task
```http
GET /tasks/{task_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "task_123456",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication system with OAuth2 integration",
    "type": "implementation",
    "status": "in_progress",
    "priority": "high",
    "assignee_role": "implementer",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T11:00:00Z",
    "created_by": "user_123",
    "assigned_to": "agent_implementer_123",
    "files_to_modify": [
      "services/orchestrator/auth.py",
      "services/console/src/auth/index.ts"
    ],
    "acceptance_criteria": [
      "Users can register with email/password",
      "OAuth2 integration works with Google",
      "JWT tokens are properly validated",
      "Refresh token mechanism implemented"
    ],
    "progress": {
      "completed_steps": 2,
      "total_steps": 4,
      "percentage": 50
    },
    "results": {
      "files_modified": 2,
      "tests_added": 4,
      "documentation_updated": true
    },
    "metadata": {
      "estimated_hours": 8,
      "actual_hours": 3.5,
      "complexity": "medium",
      "model_used": "glm-4.5",
      "cost": 0.85
    }
  }
}
```

### List Tasks
```http
GET /tasks
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Query Parameters:
# - status: pending, in_progress, completed, failed
# - type: implementation, review, design, testing
# - priority: low, medium, high, critical
# - assignee_role: architect, implementer, critic, integrator
# - created_by: user_id
# - tags: comma-separated tags
# - limit: number of results (default: 50, max: 200)
# - offset: pagination offset
# - sort_by: created_at, updated_at, priority, deadline
# - sort_order: asc, desc
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "id": "task_123456",
        "title": "Implement user authentication",
        "status": "in_progress",
        "type": "implementation",
        "priority": "high",
        "assignee_role": "implementer",
        "created_at": "2024-01-15T10:30:00Z",
        "deadline": "2024-01-20T23:59:59Z"
      }
    ],
    "pagination": {
      "total": 25,
      "limit": 50,
      "offset": 0,
      "has_more": false
    }
  }
}
```

### Update Task
```http
PUT /tasks/{task_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "status": "completed",
  "results": {
    "files_modified": 3,
    "tests_added": 6,
    "documentation_updated": true,
    "code_quality_score": 95
  },
  "feedback": "Implementation completed successfully. All tests passing."
}
```

### Cancel Task
```http
DELETE /tasks/{task_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "reason": "No longer needed due to requirement changes"
}
```

## Agent Coordination API

### Submit Task to Agent
```http
POST /agents/{role}/submit
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "task_id": "task_123456",
  "context": {
    "repository_state": "main branch at commit abc123",
    "recent_changes": [
      "feat: Added user model",
      "fix: Fixed authentication bug"
    ],
    "team_context": {
      "team_size": 5,
      "active_sprints": ["Sprint 12"],
      "code_standards": "Follow PEP 8 and ESLint rules"
    }
  },
  "preferences": {
    "model": "glm-4.5",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 300
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "submission_id": "sub_123456",
    "task_id": "task_123456",
    "role": "implementer",
    "agent_id": "agent_implementer_123",
    "status": "accepted",
    "estimated_duration": 600,
    "model_assigned": "glm-4.5",
    "submitted_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Agent Status
```http
GET /agents/{role}/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "role": "implementer",
    "available_agents": 3,
    "active_tasks": 2,
    "queue_length": 1,
    "average_response_time": 45.2,
    "success_rate": 98.5,
    "current_models": {
      "glm-4.5": 95,
      "claude-4.1-opus": 5
    },
    "performance": {
      "tasks_completed_today": 15,
      "average_task_duration": 8.5,
      "cost_per_task": 0.85
    }
  }
}
```

### Get Agent Configuration
```http
GET /agents/{role}/configuration
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "role": "implementer",
    "default_model": "glm-4.5",
    "available_models": ["glm-4.5", "claude-4.1-opus"],
    "capabilities": [
      "code_implementation",
      "test_creation",
      "bug_fixes",
      "documentation_updates"
    ],
    "preferences": {
      "temperature": 0.7,
      "max_tokens": 2000,
      "timeout": 300
    },
    "constraints": {
      "max_files_per_task": 10,
      "max_diff_size": 500,
      "allowed_file_types": [".py", ".js", ".ts", ".md"]
    },
    "escalation_rules": {
      "security_threshold": 0.8,
      "complexity_threshold": 0.7,
      "business_impact_threshold": 0.6
    }
  }
}
```

### Update Agent Configuration
```http
PUT /agents/{role}/configuration
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "default_model": "glm-4.5",
  "preferences": {
    "temperature": 0.8,
    "max_tokens": 2500,
    "timeout": 600
  },
  "escalation_rules": {
    "security_threshold": 0.9,
    "complexity_threshold": 0.8
  }
}
```

## Model Selection API

### Select Model for Task
```http
POST /models/select
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "task_description": "Implement OAuth2 authentication with SAML integration",
  "task_type": "implementation",
  "files_to_modify": [
    "auth.py",
    "security/oauth2.py",
    "security/saml.py"
  ],
  "complexity_indicators": {
    "file_count": 3,
    "service_count": 2,
    "security_sensitive": true,
    "business_critical": true
  },
  "context": {
    "deadline": "2024-01-20T23:59:59Z",
    "team_experience": "medium",
    "budget_remaining": 100.0
  },
  "preferences": {
    "cost_sensitive": true,
    "quality_critical": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "selected_model": "claude-4.1-opus",
    "confidence_score": 0.85,
    "reasoning": {
      "security_sensitive": true,
      "complexity_score": 0.82,
      "business_impact": "high",
      "cost_benefit_ratio": "favorable"
    },
    "estimated_cost": 12.50,
    "estimated_duration": 900,
    "fallback_model": "glm-4.5"
  }
}
```

### Get Model Information
```http
GET /models/{model_name}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "glm-4.5",
    "provider": "GLM",
    "capabilities": [
      "code_generation",
      "documentation",
      "testing",
      "bug_fixes"
    ],
    "limits": {
      "max_tokens": 8192,
      "requests_per_minute": 60,
      "tokens_per_minute": 120000
    },
    "pricing": {
      "input_tokens": 0.001,
      "output_tokens": 0.002,
      "currency": "USD"
    },
    "performance": {
      "average_response_time": 2.5,
      "success_rate": 99.2,
      "quality_score": 8.5
    }
  }
}
```

### List Available Models
```http
GET /models
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "glm-4.5",
        "provider": "GLM",
        "status": "available",
        "recommended_usage": "general_purpose"
      },
      {
        "name": "claude-4.1-opus",
        "provider": "Anthropic",
        "status": "available",
        "recommended_usage": "complex_tasks"
      }
    ],
    "default_model": "glm-4.5",
    "escalation_model": "claude-4.1-opus"
  }
}
```

## Escalation API

### Submit Escalation Request
```http
POST /escalation/submit
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "task_id": "task_123456",
  "original_model": "glm-4.5",
  "target_model": "claude-4.1-opus",
  "reason": "Security-critical authentication implementation with OAuth2 and SAML integration",
  "context": {
    "security_impact": "high",
    "complexity_score": 0.85,
    "business_critical": true,
    "files_affected": ["auth.py", "security/"]
  },
  "estimated_cost": 15.00,
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "escalation_id": "esc_123456",
    "task_id": "task_123456",
    "status": "pending_approval",
    "submitted_at": "2024-01-15T10:30:00Z",
    "estimated_cost": 15.00,
    "approval_required": true,
    "workflow_id": "wf_123456"
  }
}
```

### Approve Escalation
```http
POST /escalation/{escalation_id}/approve
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "decision": "approved",
  "reason": "Security-critical task with high business impact",
  "approver_comments": "Approved due to security complexity and business criticality"
}
```

### Get Escalation Status
```http
GET /escalation/{escalation_id}/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "escalation_id": "esc_123456",
    "task_id": "task_123456",
    "status": "approved",
    "original_model": "glm-4.5",
    "target_model": "claude-4.1-opus",
    "submitted_at": "2024-01-15T10:30:00Z",
    "approved_at": "2024-01-15T10:35:00Z",
    "approved_by": "user_456",
    "estimated_cost": 15.00,
    "actual_cost": 14.75,
    "result": "Task completed successfully with premium model"
  }
}
```

### List Escalations
```http
GET /escalations
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Query Parameters:
# - status: pending, approved, rejected, completed
# - task_id: task identifier
# - from_date: start date filter
# - to_date: end date filter
# - limit: pagination limit
# - offset: pagination offset
```

## Monitoring API

### Get System Health
```http
GET /monitoring/health
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy",
    "services": {
      "orchestrator": {
        "status": "healthy",
        "response_time": 45,
        "uptime": 99.9
      },
      "console": {
        "status": "healthy",
        "response_time": 120,
        "uptime": 99.8
      },
      "terminal_daemon": {
        "status": "healthy",
        "response_time": 25,
        "uptime": 99.9
      }
    },
    "database": {
      "status": "healthy",
      "connection_pool": {
        "active": 5,
        "idle": 15,
        "max": 20
      },
      "query_performance": {
        "average_time": 25,
        "slow_queries": 0
      }
    },
    "models": {
      "glm-4.5": {
        "status": "available",
        "response_time": 2.5,
        "success_rate": 99.2
      },
      "claude-4.1-opus": {
        "status": "available",
        "response_time": 3.2,
        "success_rate": 98.8
      }
    }
  }
}
```

### Get Performance Metrics
```http
GET /monitoring/metrics
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Query Parameters:
# - period: 1h, 24h, 7d, 30d
# - granularity: 1m, 5m, 1h, 1d
# - metrics: comma-separated metric names
```

**Response:**
```json
{
  "success": true,
  "data": {
    "period": "24h",
    "granularity": "1h",
    "metrics": {
      "task_completion_rate": {
        "data": [85, 90, 88, 92, 89, 94, 91, 87, 93, 90, 92, 88, 91, 89, 93, 95, 92, 90, 94, 91, 88, 93, 90, 92],
        "unit": "percent",
        "average": 90.8
      },
      "average_response_time": {
        "data": [2.1, 2.3, 2.0, 2.4, 2.2, 2.1, 2.3, 2.0, 2.4, 2.2, 2.1, 2.3, 2.0, 2.4, 2.2, 2.1, 2.3, 2.0, 2.4, 2.2, 2.1, 2.3, 2.0, 2.4],
        "unit": "seconds",
        "average": 2.2
      },
      "cost_per_task": {
        "data": [0.85, 0.90, 0.82, 0.95, 0.88, 0.85, 0.92, 0.80, 0.94, 0.87, 0.85, 0.90, 0.82, 0.95, 0.88, 0.85, 0.92, 0.80, 0.94, 0.87, 0.85, 0.90, 0.82, 0.95],
        "unit": "USD",
        "average": 0.88
      },
      "escalation_rate": {
        "data": [3.2, 4.1, 2.8, 5.2, 3.9, 3.2, 4.5, 2.9, 5.1, 3.8, 3.2, 4.1, 2.8, 5.2, 3.9, 3.2, 4.5, 2.9, 5.1, 3.8, 3.2, 4.1, 2.8, 5.2],
        "unit": "percent",
        "average": 4.0
      }
    }
  }
}
```

### Get Cost Analysis
```http
GET /monitoring/costs
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Query Parameters:
# - period: 1d, 7d, 30d, 90d
# - group_by: model, role, task_type, user
```

**Response:**
```json
{
  "success": true,
  "data": {
    "period": "7d",
    "total_cost": 342.50,
    "cost_breakdown": {
      "by_model": {
        "glm-4.5": {
          "cost": 289.12,
          "percentage": 84.4,
          "tasks": 342
        },
        "claude-4.1-opus": {
          "cost": 53.38,
          "percentage": 15.6,
          "tasks": 18
        }
      },
      "by_role": {
        "implementer": {
          "cost": 156.80,
          "percentage": 45.8,
          "tasks": 187
        },
        "architect": {
          "cost": 89.20,
          "percentage": 26.0,
          "tasks": 98
        },
        "critic": {
          "cost": 67.30,
          "percentage": 19.6,
          "tasks": 45
        },
        "integrator": {
          "cost": 29.20,
          "percentage": 8.6,
          "tasks": 30
        }
      },
      "savings": {
        "vs_premium_only": 524.30,
        "percentage": 60.5,
        "roi": 76.2
      }
    }
  }
}
```

### Get Alerts
```http
GET /monitoring/alerts
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Query Parameters:
# - status: active, resolved, acknowledged
# - severity: info, warning, error, critical
# - limit: pagination limit
# - offset: pagination offset
```

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert_123",
        "type": "cost_overrun",
        "severity": "warning",
        "status": "active",
        "message": "Daily cost exceeded budget by 20%",
        "details": {
          "budget": 50.00,
          "actual": 60.00,
          "overrun": 10.00
        },
        "created_at": "2024-01-15T10:30:00Z",
        "acknowledged_at": null,
        "resolved_at": null
      }
    ]
  }
}
```

## Configuration API

### Get System Configuration
```http
GET /configuration
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "version": "1.0.0",
      "environment": "production",
      "timezone": "UTC",
      "maintenance_mode": false
    },
    "models": {
      "default_model": "glm-4.5",
      "escalation_model": "claude-4.1-opus",
      "fallback_model": "glm-4.5",
      "timeout": 300
    },
    "escalation": {
      "auto_approve_threshold": 0.8,
      "max_daily_escalations": 10,
      "cost_threshold": 20.00,
      "approval_required": true
    },
    "monitoring": {
      "metrics_retention_days": 90,
      "alert_enabled": true,
      "performance_tracking": true
    },
    "security": {
      "jwt_expiration_hours": 24,
      "max_login_attempts": 5,
      "session_timeout_minutes": 30
    }
  }
}
```

### Update Configuration
```http
PUT /configuration
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "models": {
    "timeout": 600
  },
  "escalation": {
    "auto_approve_threshold": 0.9,
    "cost_threshold": 25.00
  },
  "monitoring": {
    "alert_enabled": true,
    "performance_tracking": true
  }
}
```

### Get Agent Role Configuration
```http
GET /configuration/agents/{role}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "role": "implementer",
    "enabled": true,
    "default_model": "glm-4.5",
    "capabilities": [
      "code_implementation",
      "test_creation",
      "bug_fixes",
      "documentation_updates"
    ],
    "constraints": {
      "max_files_per_task": 10,
      "max_diff_size": 500,
      "allowed_file_types": [".py", ".js", ".ts", ".md", ".json", ".yaml"]
    },
    "preferences": {
      "temperature": 0.7,
      "max_tokens": 2000,
      "timeout": 300
    }
  }
}
```

## Webhooks

### Create Webhook
```http
POST /webhooks
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "url": "https://your-webhook-endpoint.com/kyros-events",
  "events": [
    "task.created",
    "task.completed",
    "task.failed",
    "escalation.approved",
    "escalation.rejected"
  ],
  "secret": "your_webhook_secret",
  "description": "Webhook for task and escalation events"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "webhook_123",
    "url": "https://your-webhook-endpoint.com/kyros-events",
    "events": ["task.created", "task.completed", "task.failed", "escalation.approved", "escalation.rejected"],
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "last_triggered": null
  }
}
```

### List Webhooks
```http
GET /webhooks
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Update Webhook
```http
PUT /webhooks/{webhook_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "events": ["task.created", "task.completed"],
  "status": "paused"
}
```

### Delete Webhook
```http
DELETE /webhooks/{webhook_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Test Webhook
```http
POST /webhooks/{webhook_id}/test
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## WebSocket API

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onopen = function() {
  // Authenticate
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'your_jwt_token'
  }));
};
```

### Subscribe to Events
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  events: ['task_progress', 'escalation_status', 'system_alerts']
}));
```

### WebSocket Message Types

**Authentication:**
```json
{
  "type": "auth",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Subscription:**
```json
{
  "type": "subscribe",
  "events": ["task_progress", "escalation_status"]
}
```

**Task Progress Update:**
```json
{
  "type": "task_progress",
  "data": {
    "task_id": "task_123456",
    "status": "in_progress",
    "progress": {
      "completed_steps": 3,
      "total_steps": 5,
      "percentage": 60
    },
    "current_step": "Implementing OAuth2 integration",
    "estimated_completion": "2024-01-15T12:00:00Z"
  },
  "timestamp": "2024-01-15T11:45:00Z"
}
```

**Escalation Status Update:**
```json
{
  "type": "escalation_status",
  "data": {
    "escalation_id": "esc_123456",
    "task_id": "task_123456",
    "status": "approved",
    "approved_by": "user_456",
    "approved_at": "2024-01-15T11:45:00Z"
  },
  "timestamp": "2024-01-15T11:45:00Z"
}
```

## Error Handling

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required or failed |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `TASK_NOT_FOUND` | 404 | Task not found |
| `AGENT_UNAVAILABLE` | 503 | Agent not available |
| `MODEL_UNAVAILABLE` | 503 | Model not available |
| `ESCALATION_REJECTED` | 400 | Escalation request rejected |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "priority",
      "issue": "Must be one of: low, medium, high, critical"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Rate Limiting

### Rate Limit Headers
All API responses include rate limiting headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642249200
```

### Rate Limit by Endpoint
- **Authentication endpoints**: 5 requests per minute
- **Task creation**: 100 requests per hour
- **Model selection**: 200 requests per hour
- **Monitoring endpoints**: 1000 requests per hour
- **Webhooks**: 100 requests per minute

### Webhook Rate Limiting
- **Webhook delivery**: 50 requests per minute per endpoint
- **Retries**: Exponential backoff up to 24 hours

## Integration Examples

### Python Integration

```python
import requests
import json
from typing import Dict, Any

class KyrosClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        response = self.session.post(
            f'{self.base_url}/v1/tasks',
            json=task_data
        )
        response.raise_for_status()
        return response.json()
    
    def submit_to_agent(self, role: str, task_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Submit task to specific agent"""
        response = self.session.post(
            f'{self.base_url}/v1/agents/{role}/submit',
            json={
                'task_id': task_id,
                'context': context
            }
        )
        response.raise_for_status()
        return response.json()
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        response = self.session.get(f'{self.base_url}/v1/tasks/{task_id}')
        response.raise_for_status()
        return response.json()
    
    def request_escalation(self, task_id: str, reason: str) -> Dict[str, Any]:
        """Request task escalation"""
        response = self.session.post(
            f'{self.base_url}/v1/escalation/submit',
            json={
                'task_id': task_id,
                'reason': reason
            }
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = KyrosClient('https://api.kyros.com', 'your-api-key')

# Create a task
task = client.create_task({
    'title': 'Implement user authentication',
    'description': 'Add JWT authentication with OAuth2',
    'type': 'implementation',
    'priority': 'high',
    'assignee_role': 'implementer'
})

# Submit to agent
submission = client.submit_to_agent(
    'implementer',
    task['data']['id'],
    {'repository_state': 'main branch at abc123'}
)

# Monitor progress
while True:
    status = client.get_task_status(task['data']['id'])
    print(f"Task status: {status['data']['status']}")
    if status['data']['status'] in ['completed', 'failed']:
        break
    time.sleep(30)
```

### JavaScript Integration

```javascript
class KyrosAPI {
    constructor(baseURL, apiKey) {
        this.baseURL = baseURL.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.defaultHeaders = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}/v1${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                ...this.defaultHeaders,
                ...options.headers
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'API request failed');
        }

        return response.json();
    }

    async createTask(taskData) {
        return this.request('/tasks', {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }

    async getTask(taskId) {
        return this.request(`/tasks/${taskId}`);
    }

    async submitToAgent(role, taskId, context) {
        return this.request(`/agents/${role}/submit`, {
            method: 'POST',
            body: JSON.stringify({
                task_id: taskId,
                context
            })
        });
    }

    async requestEscalation(taskId, reason) {
        return this.request('/escalation/submit', {
            method: 'POST',
            body: JSON.stringify({
                task_id: taskId,
                reason
            })
        });
    }

    async getMetrics(period = '24h') {
        return this.request(`/monitoring/metrics?period=${period}`);
    }
}

// Usage example
const kyros = new KyrosAPI('https://api.kyros.com', 'your-api-key');

async function implementAuthentication() {
    try {
        // Create task
        const task = await kyros.createTask({
            title: 'Implement user authentication',
            description: 'Add JWT authentication with OAuth2',
            type: 'implementation',
            priority: 'high',
            assignee_role: 'implementer'
        });

        console.log('Task created:', task.data.id);

        // Submit to agent
        const submission = await kyros.submitToAgent(
            'implementer',
            task.data.id,
            { repository_state: 'main branch at abc123' }
        );

        console.log('Task submitted to agent');

        // Monitor progress
        const monitorProgress = async () => {
            const status = await kyros.getTask(task.data.id);
            console.log(`Task status: ${status.data.status}`);
            
            if (status.data.status === 'completed') {
                console.log('Task completed successfully!');
                return;
            } else if (status.data.status === 'failed') {
                console.error('Task failed:', status.data.error);
                return;
            }

            setTimeout(monitorProgress, 30000);
        };

        monitorProgress();

    } catch (error) {
        console.error('Error:', error.message);
    }
}

implementAuthentication();
```

### WebSocket Integration

```javascript
class KyrosWebSocket {
    constructor(url, token) {
        this.url = url;
        this.token = token;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.eventHandlers = {};
    }

    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.authenticate();
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    authenticate() {
        this.send({
            type: 'auth',
            token: this.token
        });
    }

    subscribe(events) {
        this.send({
            type: 'subscribe',
            events: events
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    handleMessage(message) {
        const { type, data } = message;
        
        if (this.eventHandlers[type]) {
            this.eventHandlers[type].forEach(handler => handler(data));
        }
    }

    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage example
const ws = new KyrosWebSocket('ws://localhost:8000/ws', 'your-jwt-token');

ws.connect();

ws.on('open', () => {
    // Subscribe to events
    ws.subscribe(['task_progress', 'escalation_status']);
});

ws.on('task_progress', (data) => {
    console.log('Task progress update:', data);
    // Update UI with progress information
});

ws.on('escalation_status', (data) => {
    console.log('Escalation status update:', data);
    // Handle escalation notifications
});

ws.on('system_alerts', (data) => {
    console.log('System alert:', data);
    // Show alerts to users
});
```

### CLI Integration

```bash
#!/bin/bash

# Kyros CLI Integration Script

KYROS_API_URL="https://api.kyros.com"
KYROS_API_KEY="your-api-key"

# Create task
create_task() {
    local title="$1"
    local description="$2"
    local role="${3:-implementer}"
    local priority="${4:-medium}"
    
    curl -X POST "$KYROS_API_URL/v1/tasks" \
        -H "Authorization: Bearer $KYROS_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"title\": \"$title\",
            \"description\": \"$description\",
            \"type\": \"implementation\",
            \"priority\": \"$priority\",
            \"assignee_role\": \"$role\"
        }"
}

# Get task status
get_task_status() {
    local task_id="$1"
    
    curl -X GET "$KYROS_API_URL/v1/tasks/$task_id" \
        -H "Authorization: Bearer $KYROS_API_KEY"
}

# Request escalation
request_escalation() {
    local task_id="$1"
    local reason="$2"
    
    curl -X POST "$KYROS_API_URL/v1/escalation/submit" \
        -H "Authorization: Bearer $KYROS_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"task_id\": \"$task_id\",
            \"reason\": \"$reason\"
        }"
}

# Get cost analysis
get_cost_analysis() {
    local period="${1:-7d}"
    
    curl -X GET "$KYROS_API_URL/v1/monitoring/costs?period=$period" \
        -H "Authorization: Bearer $KYROS_API_KEY"
}

# Monitor task
monitor_task() {
    local task_id="$1"
    local interval="${2:-30}"
    
    while true; do
        local status=$(get_task_status "$task_id" | jq -r '.data.status')
        echo "Task $task_id status: $status"
        
        if [[ "$status" == "completed" || "$status" == "failed" ]]; then
            break
        fi
        
        sleep "$interval"
    done
}

# Usage examples
echo "Creating task..."
TASK_RESPONSE=$(create_task "Implement user authentication" "Add JWT authentication system" implementer high)
TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.data.id')
echo "Task created with ID: $TASK_ID"

echo "Monitoring task..."
monitor_task "$TASK_ID"

echo "Getting cost analysis..."
get_cost_analysis "7d" | jq '.'
```

---

## API Changelog

### Version 1.0.0 (2024-01-15)
- Initial API release
- Task management endpoints
- Agent coordination endpoints
- Model selection and escalation
- Monitoring and configuration
- WebSocket support
- Webhook integration