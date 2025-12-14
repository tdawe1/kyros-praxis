// Package models defines the request and response types for the API.
package models

import (
	"time"

	"github.com/google/uuid"
)

// User represents a user in the system.
type User struct {
	ID           uuid.UUID `json:"id"`
	Username     string    `json:"username"`
	Email        string    `json:"email"`
	PasswordHash string    `json:"-"` // Never expose
	Role         string    `json:"role"`
	Active       bool      `json:"active"`
	CreatedAt    time.Time `json:"created_at"`
}

// Project represents a multi-agent project.
type Project struct {
	ID          uuid.UUID  `json:"id"`
	UserID      *uuid.UUID `json:"user_id,omitempty"`
	Name        string     `json:"name"`
	Description string     `json:"description"`
	Status      string     `json:"status"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
}

// Task represents a task within a project.
type Task struct {
	ID          uuid.UUID `json:"id"`
	ProjectID   uuid.UUID `json:"project_id"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Priority    string    `json:"priority"`
	Status      string    `json:"status"`
	CreatedAt   time.Time `json:"created_at"`
}

// ---- Request Types ----

// RegisterRequest is the request body for user registration.
type RegisterRequest struct {
	Username string `json:"username" validate:"required,min=3,max=50"`
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required,min=8"`
}

// LoginRequest is the request body for user login.
type LoginRequest struct {
	Email    string `json:"email" validate:"required,email"`
	Password string `json:"password" validate:"required"`
}

// RefreshRequest is the request body for token refresh.
type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" validate:"required"`
}

// CreateProjectRequest is the request body for creating a project.
type CreateProjectRequest struct {
	Name        string `json:"name" validate:"required,min=1,max=255"`
	Description string `json:"description"`
}

// UpdateProjectRequest is the request body for updating a project.
type UpdateProjectRequest struct {
	Name        *string `json:"name,omitempty" validate:"omitempty,min=1,max=255"`
	Description *string `json:"description,omitempty"`
	Status      *string `json:"status,omitempty"`
}

// CreateTaskRequest is the request body for creating a task.
type CreateTaskRequest struct {
	Title       string `json:"title" validate:"required,min=1,max=255"`
	Description string `json:"description"`
	Priority    string `json:"priority" validate:"omitempty,oneof=P0 P1 P2 P3"`
}

// UpdateTaskRequest is the request body for updating a task.
type UpdateTaskRequest struct {
	Title       *string `json:"title,omitempty" validate:"omitempty,min=1,max=255"`
	Description *string `json:"description,omitempty"`
	Priority    *string `json:"priority,omitempty" validate:"omitempty,oneof=P0 P1 P2 P3"`
	Status      *string `json:"status,omitempty"`
}

// WorkflowGenerateRequest is the request to start workflow generation.
type WorkflowGenerateRequest struct {
	Prompt string `json:"prompt" validate:"required,min=10"`
}

// WorkflowApproveRequest is the request to approve a specification.
type WorkflowApproveRequest struct {
	Approved      bool                   `json:"approved"`
	Specification map[string]interface{} `json:"specification"`
}

// WorkflowRefineRequest is the request to refine a workflow.
type WorkflowRefineRequest struct {
	RefinementNotes string `json:"refinement_notes" validate:"required,min=10"`
}

// ---- Response Types ----

// TokenResponse is the response for authentication endpoints.
type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	TokenType    string `json:"token_type"`
	RefreshToken string `json:"refresh_token,omitempty"`
	ExpiresIn    int    `json:"expires_in"`
}

// UserResponse is the public user information.
type UserResponse struct {
	ID        uuid.UUID `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	Role      string    `json:"role"`
	Active    bool      `json:"active"`
	CreatedAt string    `json:"created_at"`
}

// HealthResponse is the response for the health endpoint.
type HealthResponse struct {
	Status   string                 `json:"status"`
	Env      string                 `json:"env"`
	Features map[string]interface{} `json:"features,omitempty"`
}

// ErrorResponse is the standard error response format.
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
	Details string `json:"details,omitempty"`
}

// DashboardResponse contains project dashboard data.
type DashboardResponse struct {
	Project        Project                  `json:"project"`
	Tasks          []Task                   `json:"tasks"`
	TotalTasks     int                      `json:"total_tasks"`
	CompletedTasks int                      `json:"completed_tasks"`
	ActiveRuns     int                      `json:"active_runs"`
	Artifacts      []map[string]interface{} `json:"artifacts"`
}

// ProvidersResponse lists available LLM providers.
type ProvidersResponse struct {
	CurrentProvider string                    `json:"current_provider"`
	CurrentModel    string                    `json:"current_model"`
	CurrentValid    bool                      `json:"current_valid"`
	CurrentMissing  []string                  `json:"current_missing"`
	Providers       map[string]ProviderStatus `json:"providers"`
}

// ProviderStatus shows configuration status of a provider.
type ProviderStatus struct {
	Configured    bool     `json:"configured"`
	MissingConfig []string `json:"missing_config"`
	DefaultModel  string   `json:"default_model"`
}
