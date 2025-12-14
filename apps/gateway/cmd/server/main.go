// Package main is the entry point for the Kyros Praxis API Gateway.
package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/cors"
	"github.com/kyros-praxis/gateway/internal/auth"
	"github.com/kyros-praxis/gateway/internal/config"
	"github.com/kyros-praxis/gateway/internal/db"
	"github.com/kyros-praxis/gateway/internal/handlers"
	"github.com/kyros-praxis/gateway/internal/middleware"
)

func main() {
	// Initialize logger
	log := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(log)

	// Load configuration
	cfg := config.Load()
	log.Info("configuration loaded",
		"env", cfg.Environment,
		"port", cfg.Port,
	)

	// Connect to database
	database, err := db.New(cfg.DatabaseURL)
	if err != nil {
		log.Error("failed to connect to database", "error", err)
		os.Exit(1)
	}
	defer database.Close()
	log.Info("database connected")

	// Initialize auth service
	authService := auth.New(cfg, database)

	// Initialize handlers
	h := handlers.New(cfg, database, authService, log)

	// Initialize router
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Recoverer(log))
	r.Use(middleware.Logger(log))
	r.Use(middleware.NewRateLimiter(cfg.RateLimitRPM).Middleware)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   cfg.CORSAllowOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: true,
		MaxAge:           300,
	}))
	r.Use(authService.Middleware)

	// Routes
	r.Get("/health", h.Health)

	// Auth routes
	r.Route("/auth", func(r chi.Router) {
		r.Post("/register", h.Register)
		r.Post("/login", h.Login)
		r.With(authService.RequireAuth).Get("/me", h.GetMe)
	})

	// Project routes
	r.Route("/projects", func(r chi.Router) {
		r.Get("/", h.ListProjects)
		r.With(authService.RequireAuth).Post("/", h.CreateProject)
		r.Get("/{id}", h.GetProject)

		// Task routes
		r.With(authService.RequireAuth).Post("/{id}/tasks", h.CreateTask)
		r.Get("/{id}/tasks", h.ListTasks)
		r.With(authService.RequireAuth).Get("/{id}/dashboard", h.GetDashboard)
	})

	// Admin routes
	r.Get("/admin/providers", h.GetProviders)

	// Create server
	server := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Info("server starting", "addr", server.Addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Error("server error", "error", err)
			os.Exit(1)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("shutting down server...")

	// Graceful shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Error("server forced to shutdown", "error", err)
	}

	log.Info("server stopped")
}
