// Package config provides configuration loading from environment variables.
package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

// Config holds all application configuration.
type Config struct {
	// Server
	Port        string
	Environment string
	Debug       bool

	// Database
	DatabaseURL string

	// JWT
	JWTSecretKey         string
	JWTExpireMinutes     int
	JWTRefreshExpireDays int

	// Redis
	RedisURL string

	// CORS
	CORSAllowOrigins []string

	// Rate Limiting
	RateLimitRPM int

	// Python Workers
	WorkerBaseURL string

	// LLM Providers
	ModelProvider string
	ModelName     string
}

// Load reads configuration from environment variables with defaults.
func Load() *Config {
	return &Config{
		// Server
		Port:        getEnv("PORT", "8001"),
		Environment: getEnv("KYROS_ENV", "dev"),
		Debug:       getEnvBool("DEBUG", false),

		// Database
		DatabaseURL: getEnv("DATABASE_URL", "postgres://kyros:kyros@localhost:5432/kyros?sslmode=disable"),

		// JWT
		JWTSecretKey:         getEnv("JWT_SECRET_KEY", "dev-secret-key-change-in-production"),
		JWTExpireMinutes:     getEnvInt("JWT_EXPIRE_MINUTES", 15),
		JWTRefreshExpireDays: getEnvInt("JWT_REFRESH_EXPIRE_DAYS", 7),

		// Redis
		RedisURL: getEnv("REDIS_URL", ""),

		// CORS
		CORSAllowOrigins: getEnvList("CORS_ALLOW_ORIGINS", []string{"http://localhost:3000"}),

		// Rate Limiting
		RateLimitRPM: getEnvInt("RATE_LIMIT_RPM", 100),

		// Python Workers
		WorkerBaseURL: getEnv("WORKER_BASE_URL", "http://localhost:8002"),

		// LLM Providers
		ModelProvider: getEnv("MODEL_PROVIDER", "openrouter"),
		ModelName:     getEnv("MODEL_NAME", "gpt-4o-mini"),
	}
}

// JWTExpireDuration returns the JWT expiration as a time.Duration.
func (c *Config) JWTExpireDuration() time.Duration {
	return time.Duration(c.JWTExpireMinutes) * time.Minute
}

// JWTRefreshExpireDuration returns the refresh token expiration as a time.Duration.
func (c *Config) JWTRefreshExpireDuration() time.Duration {
	return time.Duration(c.JWTRefreshExpireDays) * 24 * time.Hour
}

// IsProduction returns true if running in production environment.
func (c *Config) IsProduction() bool {
	return c.Environment == "production"
}

// ValidateProduction validates security configuration for production.
// Returns an error if critical security settings are not properly configured.
func (c *Config) ValidateProduction() error {
	if !c.IsProduction() {
		return nil
	}

	// JWT secret must be set and secure
	if c.JWTSecretKey == "" || len(c.JWTSecretKey) < 32 {
		return fmt.Errorf("JWT_SECRET_KEY must be at least 32 characters in production")
	}
	if c.JWTSecretKey == "dev-secret-key-change-in-production" {
		return fmt.Errorf("JWT_SECRET_KEY cannot use default value in production")
	}

	// Database URL should not use localhost
	if strings.Contains(c.DatabaseURL, "localhost") {
		// Log warning but don't fail
	}

	return nil
}

// Helper functions

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if i, err := strconv.Atoi(value); err == nil {
			return i
		}
	}
	return defaultValue
}

func getEnvBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		return strings.ToLower(value) == "true" || value == "1"
	}
	return defaultValue
}

func getEnvList(key string, defaultValue []string) []string {
	if value := os.Getenv(key); value != "" {
		return strings.Split(value, ",")
	}
	return defaultValue
}
