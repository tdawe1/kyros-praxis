// Package handlers provides HTTP handlers for the API.
package handlers

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"github.com/google/uuid"
	"github.com/kyros-praxis/gateway/internal/auth"
	"github.com/kyros-praxis/gateway/internal/config"
	"github.com/kyros-praxis/gateway/internal/db"
	"github.com/kyros-praxis/gateway/internal/models"
)

// Handler holds dependencies for HTTP handlers.
type Handler struct {
	cfg      *config.Config
	db       *db.DB
	auth     *auth.Auth
	validate *validator.Validate
	log      *slog.Logger
}

// New creates a new Handler.
func New(cfg *config.Config, database *db.DB, authService *auth.Auth, log *slog.Logger) *Handler {
	return &Handler{
		cfg:      cfg,
		db:       database,
		auth:     authService,
		validate: validator.New(),
		log:      log,
	}
}

// ---- Helper Functions ----

func (h *Handler) writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func (h *Handler) writeError(w http.ResponseWriter, status int, err string, message string) {
	h.writeJSON(w, status, models.ErrorResponse{
		Error:   err,
		Message: message,
	})
}

func (h *Handler) decodeAndValidate(r *http.Request, v interface{}) error {
	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		return err
	}
	return h.validate.Struct(v)
}

// ---- Health ----

// Health handles GET /health.
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	h.writeJSON(w, http.StatusOK, models.HealthResponse{
		Status: "ok",
		Env:    h.cfg.Environment,
		Features: map[string]interface{}{
			"rate_limiting":   true,
			"metrics":         true,
			"caching":         h.cfg.RedisURL != "",
			"background_jobs": true,
		},
	})
}

// ---- Auth Handlers ----

// Register handles POST /auth/register.
func (h *Handler) Register(w http.ResponseWriter, r *http.Request) {
	var req models.RegisterRequest
	if err := h.decodeAndValidate(r, &req); err != nil {
		h.writeError(w, http.StatusBadRequest, "validation_error", err.Error())
		return
	}

	// Check if user exists
	if existing, _ := h.db.GetUserByEmail(r.Context(), req.Email); existing != nil {
		h.writeError(w, http.StatusBadRequest, "email_exists", "Email already registered")
		return
	}
	if existing, _ := h.db.GetUserByUsername(r.Context(), req.Username); existing != nil {
		h.writeError(w, http.StatusBadRequest, "username_exists", "Username already registered")
		return
	}

	// Hash password
	hash, err := auth.HashPassword(req.Password)
	if err != nil {
		h.log.Error("failed to hash password", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to create user")
		return
	}

	// Create user
	user := &models.User{
		ID:           uuid.New(),
		Username:     req.Username,
		Email:        req.Email,
		PasswordHash: hash,
		Role:         "user",
		Active:       true,
		CreatedAt:    time.Now().UTC(),
	}

	if err := h.db.CreateUser(r.Context(), user); err != nil {
		h.log.Error("failed to create user", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to create user")
		return
	}

	h.writeJSON(w, http.StatusCreated, models.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt.Format(time.RFC3339),
	})
}

// Login handles POST /auth/login.
func (h *Handler) Login(w http.ResponseWriter, r *http.Request) {
	var req models.LoginRequest
	if err := h.decodeAndValidate(r, &req); err != nil {
		h.writeError(w, http.StatusBadRequest, "validation_error", err.Error())
		return
	}

	// Get user
	user, err := h.db.GetUserByEmail(r.Context(), req.Email)
	if err != nil || !auth.CheckPassword(req.Password, user.PasswordHash) {
		h.writeError(w, http.StatusUnauthorized, "invalid_credentials", "Incorrect email or password")
		return
	}

	// Create tokens
	accessToken, err := h.auth.CreateAccessToken(user)
	if err != nil {
		h.log.Error("failed to create access token", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to create token")
		return
	}

	refreshToken, err := h.auth.CreateRefreshToken(user)
	if err != nil {
		h.log.Error("failed to create refresh token", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to create token")
		return
	}

	// Set cookie
	http.SetCookie(w, &http.Cookie{
		Name:     "access_token",
		Value:    accessToken,
		Path:     "/",
		HttpOnly: true,
		Secure:   h.cfg.IsProduction(),
		SameSite: http.SameSiteLaxMode,
		MaxAge:   h.cfg.JWTExpireMinutes * 60,
	})

	h.writeJSON(w, http.StatusOK, models.TokenResponse{
		AccessToken:  accessToken,
		TokenType:    "bearer",
		RefreshToken: refreshToken,
		ExpiresIn:    h.cfg.JWTExpireMinutes * 60,
	})
}

// GetMe handles GET /auth/me.
func (h *Handler) GetMe(w http.ResponseWriter, r *http.Request) {
	user := auth.GetUserFromContext(r.Context())
	if user == nil {
		h.writeError(w, http.StatusUnauthorized, "unauthorized", "Not authenticated")
		return
	}

	h.writeJSON(w, http.StatusOK, models.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		Role:      user.Role,
		Active:    user.Active,
		CreatedAt: user.CreatedAt.Format(time.RFC3339),
	})
}

// ---- Project Handlers ----

// CreateProject handles POST /projects.
func (h *Handler) CreateProject(w http.ResponseWriter, r *http.Request) {
	user := auth.GetUserFromContext(r.Context())

	var req models.CreateProjectRequest
	if err := h.decodeAndValidate(r, &req); err != nil {
		h.writeError(w, http.StatusBadRequest, "validation_error", err.Error())
		return
	}

	project := &models.Project{
		ID:          uuid.New(),
		Name:        req.Name,
		Description: req.Description,
		Status:      "active",
		CreatedAt:   time.Now().UTC(),
		UpdatedAt:   time.Now().UTC(),
	}

	if user != nil {
		project.UserID = &user.ID
	}

	if err := h.db.CreateProject(r.Context(), project); err != nil {
		h.log.Error("failed to create project", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to create project")
		return
	}

	h.writeJSON(w, http.StatusCreated, project)
}

// ListProjects handles GET /projects.
func (h *Handler) ListProjects(w http.ResponseWriter, r *http.Request) {
	user := auth.GetUserFromContext(r.Context())

	var userID *uuid.UUID
	if user != nil {
		userID = &user.ID
	}

	projects, err := h.db.ListProjects(r.Context(), userID)
	if err != nil {
		h.log.Error("failed to list projects", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to list projects")
		return
	}

	if projects == nil {
		projects = []models.Project{}
	}

	h.writeJSON(w, http.StatusOK, projects)
}

// GetProject handles GET /projects/{id}.
func (h *Handler) GetProject(w http.ResponseWriter, r *http.Request) {
	projectID, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid_id", "Invalid project ID")
		return
	}

	project, err := h.db.GetProjectByID(r.Context(), projectID)
	if err != nil {
		h.writeError(w, http.StatusNotFound, "not_found", "Project not found")
		return
	}

	h.writeJSON(w, http.StatusOK, project)
}

// ---- Task Handlers ----

// CreateTask handles POST /projects/{id}/tasks.
func (h *Handler) CreateTask(w http.ResponseWriter, r *http.Request) {
	projectID, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid_id", "Invalid project ID")
		return
	}

	// Verify project exists
	if _, err := h.db.GetProjectByID(r.Context(), projectID); err != nil {
		h.writeError(w, http.StatusNotFound, "not_found", "Project not found")
		return
	}

	var req models.CreateTaskRequest
	if err := h.decodeAndValidate(r, &req); err != nil {
		h.writeError(w, http.StatusBadRequest, "validation_error", err.Error())
		return
	}

	priority := req.Priority
	if priority == "" {
		priority = "P2"
	}

	task := &models.Task{
		ID:          uuid.New(),
		ProjectID:   projectID,
		Title:       req.Title,
		Description: req.Description,
		Priority:    priority,
		Status:      "queued",
		CreatedAt:   time.Now().UTC(),
	}

	if err := h.db.CreateTask(r.Context(), task); err != nil {
		h.log.Error("failed to create task", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to create task")
		return
	}

	h.writeJSON(w, http.StatusCreated, task)
}

// ListTasks handles GET /projects/{id}/tasks.
func (h *Handler) ListTasks(w http.ResponseWriter, r *http.Request) {
	projectID, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid_id", "Invalid project ID")
		return
	}

	tasks, err := h.db.ListTasksByProject(r.Context(), projectID)
	if err != nil {
		h.log.Error("failed to list tasks", "error", err)
		h.writeError(w, http.StatusInternalServerError, "internal_error", "Failed to list tasks")
		return
	}

	if tasks == nil {
		tasks = []models.Task{}
	}

	h.writeJSON(w, http.StatusOK, tasks)
}

// GetDashboard handles GET /projects/{id}/dashboard.
func (h *Handler) GetDashboard(w http.ResponseWriter, r *http.Request) {
	projectID, err := uuid.Parse(chi.URLParam(r, "id"))
	if err != nil {
		h.writeError(w, http.StatusBadRequest, "invalid_id", "Invalid project ID")
		return
	}

	project, err := h.db.GetProjectByID(r.Context(), projectID)
	if err != nil {
		h.writeError(w, http.StatusNotFound, "not_found", "Project not found")
		return
	}

	tasks, err := h.db.ListTasksByProject(r.Context(), projectID)
	if err != nil {
		tasks = []models.Task{}
	}

	completedCount, _ := h.db.CountCompletedTasks(r.Context(), projectID)

	h.writeJSON(w, http.StatusOK, models.DashboardResponse{
		Project:        *project,
		Tasks:          tasks,
		TotalTasks:     len(tasks),
		CompletedTasks: completedCount,
		ActiveRuns:     0, // TODO: Get from workers
		Artifacts:      []map[string]interface{}{},
	})
}

// ---- Admin Handlers ----

// GetProviders handles GET /admin/providers.
func (h *Handler) GetProviders(w http.ResponseWriter, r *http.Request) {
	// Provider configuration status
	providers := map[string]models.ProviderStatus{
		"openrouter": {
			Configured:    true, // OpenRouter is default
			MissingConfig: []string{},
			DefaultModel:  "openrouter/openai/gpt-4o-mini",
		},
		"openai": {
			Configured:    false,
			MissingConfig: []string{"OPENAI_API_KEY"},
			DefaultModel:  "gpt-4o-mini",
		},
		"vertex": {
			Configured:    false,
			MissingConfig: []string{"GOOGLE_PROJECT_ID"},
			DefaultModel:  "gemini-1.5-pro",
		},
		"bedrock": {
			Configured:    true, // AWS can use IAM
			MissingConfig: []string{},
			DefaultModel:  "anthropic.claude-3-sonnet-20240229-v1:0",
		},
		"azure": {
			Configured:    false,
			MissingConfig: []string{"AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"},
			DefaultModel:  "gpt-4o",
		},
	}

	h.writeJSON(w, http.StatusOK, models.ProvidersResponse{
		CurrentProvider: h.cfg.ModelProvider,
		CurrentModel:    h.cfg.ModelName,
		CurrentValid:    true,
		CurrentMissing:  []string{},
		Providers:       providers,
	})
}
