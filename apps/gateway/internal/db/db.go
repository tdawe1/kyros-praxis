// Package db provides database connection and query functions.
package db

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/kyros-praxis/gateway/internal/models"
)

// DB wraps the database connection pool.
type DB struct {
	pool *pgxpool.Pool
}

// New creates a new database connection.
func New(databaseURL string) (*DB, error) {
	config, err := pgxpool.ParseConfig(databaseURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse database URL: %w", err)
	}

	config.MaxConns = 20
	config.MinConns = 2
	config.MaxConnLifetime = time.Hour
	config.MaxConnIdleTime = 30 * time.Minute

	pool, err := pgxpool.NewWithConfig(context.Background(), config)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	// Test connection
	if err := pool.Ping(context.Background()); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return &DB{pool: pool}, nil
}

// Close closes the database connection pool.
func (db *DB) Close() {
	db.pool.Close()
}

// ---- User Queries ----

// CreateUser inserts a new user into the database.
func (db *DB) CreateUser(ctx context.Context, user *models.User) error {
	query := `
		INSERT INTO users (id, username, email, password_hash, role, active, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err := db.pool.Exec(ctx, query,
		user.ID, user.Username, user.Email, user.PasswordHash,
		user.Role, user.Active, user.CreatedAt,
	)
	return err
}

// GetUserByEmail retrieves a user by email.
func (db *DB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at
		FROM users WHERE email = $1
	`
	var user models.User
	err := db.pool.QueryRow(ctx, query, email).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash,
		&user.Role, &user.Active, &user.CreatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// GetUserByUsername retrieves a user by username.
func (db *DB) GetUserByUsername(ctx context.Context, username string) (*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at
		FROM users WHERE username = $1
	`
	var user models.User
	err := db.pool.QueryRow(ctx, query, username).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash,
		&user.Role, &user.Active, &user.CreatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// GetUserByID retrieves a user by ID.
func (db *DB) GetUserByID(ctx context.Context, id uuid.UUID) (*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at
		FROM users WHERE id = $1
	`
	var user models.User
	err := db.pool.QueryRow(ctx, query, id).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash,
		&user.Role, &user.Active, &user.CreatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// ---- Project Queries ----

// CreateProject inserts a new project into the database.
func (db *DB) CreateProject(ctx context.Context, project *models.Project) error {
	query := `
		INSERT INTO projects (id, user_id, name, description, status, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err := db.pool.Exec(ctx, query,
		project.ID, project.UserID, project.Name, project.Description,
		project.Status, project.CreatedAt, project.UpdatedAt,
	)
	return err
}

// GetProjectByID retrieves a project by ID.
func (db *DB) GetProjectByID(ctx context.Context, id uuid.UUID) (*models.Project, error) {
	query := `
		SELECT id, user_id, name, description, status, created_at, updated_at
		FROM projects WHERE id = $1
	`
	var project models.Project
	err := db.pool.QueryRow(ctx, query, id).Scan(
		&project.ID, &project.UserID, &project.Name, &project.Description,
		&project.Status, &project.CreatedAt, &project.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &project, nil
}

// ListProjects retrieves all projects, optionally filtered by user ID.
func (db *DB) ListProjects(ctx context.Context, userID *uuid.UUID) ([]models.Project, error) {
	var query string
	var args []interface{}

	if userID != nil {
		query = `
			SELECT id, user_id, name, description, status, created_at, updated_at
			FROM projects WHERE user_id = $1
			ORDER BY created_at DESC
		`
		args = []interface{}{*userID}
	} else {
		query = `
			SELECT id, user_id, name, description, status, created_at, updated_at
			FROM projects
			ORDER BY created_at DESC
		`
	}

	rows, err := db.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var projects []models.Project
	for rows.Next() {
		var p models.Project
		if err := rows.Scan(
			&p.ID, &p.UserID, &p.Name, &p.Description,
			&p.Status, &p.CreatedAt, &p.UpdatedAt,
		); err != nil {
			return nil, err
		}
		projects = append(projects, p)
	}

	return projects, rows.Err()
}

// UpdateProject updates a project.
func (db *DB) UpdateProject(ctx context.Context, project *models.Project) error {
	query := `
		UPDATE projects
		SET name = $2, description = $3, status = $4, updated_at = $5
		WHERE id = $1
	`
	_, err := db.pool.Exec(ctx, query,
		project.ID, project.Name, project.Description,
		project.Status, project.UpdatedAt,
	)
	return err
}

// DeleteProject deletes a project by ID.
func (db *DB) DeleteProject(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM projects WHERE id = $1`
	_, err := db.pool.Exec(ctx, query, id)
	return err
}

// ---- Task Queries ----

// CreateTask inserts a new task into the database.
func (db *DB) CreateTask(ctx context.Context, task *models.Task) error {
	query := `
		INSERT INTO tasks (id, project_id, title, description, priority, status, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err := db.pool.Exec(ctx, query,
		task.ID, task.ProjectID, task.Title, task.Description,
		task.Priority, task.Status, task.CreatedAt,
	)
	return err
}

// ListTasksByProject retrieves all tasks for a project.
func (db *DB) ListTasksByProject(ctx context.Context, projectID uuid.UUID) ([]models.Task, error) {
	query := `
		SELECT id, project_id, title, description, priority, status, created_at
		FROM tasks WHERE project_id = $1
		ORDER BY created_at ASC
	`
	rows, err := db.pool.Query(ctx, query, projectID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tasks []models.Task
	for rows.Next() {
		var t models.Task
		if err := rows.Scan(
			&t.ID, &t.ProjectID, &t.Title, &t.Description,
			&t.Priority, &t.Status, &t.CreatedAt,
		); err != nil {
			return nil, err
		}
		tasks = append(tasks, t)
	}

	return tasks, rows.Err()
}

// GetTaskByID retrieves a task by ID.
func (db *DB) GetTaskByID(ctx context.Context, id uuid.UUID) (*models.Task, error) {
	query := `
		SELECT id, project_id, title, description, priority, status, created_at
		FROM tasks WHERE id = $1
	`
	var task models.Task
	err := db.pool.QueryRow(ctx, query, id).Scan(
		&task.ID, &task.ProjectID, &task.Title, &task.Description,
		&task.Priority, &task.Status, &task.CreatedAt,
	)
	if err != nil {
		return nil, err
	}
	return &task, nil
}

// UpdateTask updates a task.
func (db *DB) UpdateTask(ctx context.Context, task *models.Task) error {
	query := `
		UPDATE tasks
		SET title = $2, description = $3, priority = $4, status = $5
		WHERE id = $1
	`
	_, err := db.pool.Exec(ctx, query,
		task.ID, task.Title, task.Description, task.Priority, task.Status,
	)
	return err
}

// CountCompletedTasks counts completed tasks for a project.
func (db *DB) CountCompletedTasks(ctx context.Context, projectID uuid.UUID) (int, error) {
	query := `SELECT COUNT(*) FROM tasks WHERE project_id = $1 AND status = 'completed'`
	var count int
	err := db.pool.QueryRow(ctx, query, projectID).Scan(&count)
	return count, err
}
