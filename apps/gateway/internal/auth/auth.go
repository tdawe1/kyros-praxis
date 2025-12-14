// Package auth provides JWT authentication utilities.
package auth

import (
	"context"
	"errors"
	"net/http"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/kyros-praxis/gateway/internal/config"
	"github.com/kyros-praxis/gateway/internal/db"
	"github.com/kyros-praxis/gateway/internal/models"
	"golang.org/x/crypto/bcrypt"
)

// Context key for storing user in request context.
type contextKey string

const UserContextKey contextKey = "user"

// Claims represents the JWT claims.
type Claims struct {
	UserID uuid.UUID `json:"user_id"`
	Email  string    `json:"sub"`
	jwt.RegisteredClaims
}

// Auth provides authentication services.
type Auth struct {
	cfg *config.Config
	db  *db.DB
}

// New creates a new Auth service.
func New(cfg *config.Config, database *db.DB) *Auth {
	return &Auth{cfg: cfg, db: database}
}

// HashPassword hashes a password using bcrypt.
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// CheckPassword compares a password with a hash.
func CheckPassword(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// CreateAccessToken creates a new JWT access token.
func (a *Auth) CreateAccessToken(user *models.User) (string, error) {
	claims := Claims{
		UserID: user.ID,
		Email:  user.Email,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(a.cfg.JWTExpireDuration())),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Subject:   user.Email,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(a.cfg.JWTSecretKey))
}

// CreateRefreshToken creates a new JWT refresh token.
func (a *Auth) CreateRefreshToken(user *models.User) (string, error) {
	claims := Claims{
		UserID: user.ID,
		Email:  user.Email,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(a.cfg.JWTRefreshExpireDuration())),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			Subject:   user.Email,
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString([]byte(a.cfg.JWTSecretKey))
}

// ValidateToken validates a JWT token and returns the claims.
func (a *Auth) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return []byte(a.cfg.JWTSecretKey), nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("invalid token")
}

// Middleware returns an HTTP middleware that authenticates requests.
func (a *Auth) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Try to get token from Authorization header
		authHeader := r.Header.Get("Authorization")
		var tokenString string

		if strings.HasPrefix(authHeader, "Bearer ") {
			tokenString = strings.TrimPrefix(authHeader, "Bearer ")
		}

		// Try to get token from cookie if not in header
		if tokenString == "" {
			if cookie, err := r.Cookie("access_token"); err == nil {
				tokenString = cookie.Value
			}
		}

		// If no token found, continue without user context
		if tokenString == "" {
			next.ServeHTTP(w, r)
			return
		}

		// Validate token
		claims, err := a.ValidateToken(tokenString)
		if err != nil {
			// Token invalid, continue without user context
			next.ServeHTTP(w, r)
			return
		}

		// Get user from database
		user, err := a.db.GetUserByID(r.Context(), claims.UserID)
		if err != nil {
			next.ServeHTTP(w, r)
			return
		}

		// Add user to context
		ctx := context.WithValue(r.Context(), UserContextKey, user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequireAuth returns a middleware that requires authentication.
func (a *Auth) RequireAuth(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		user := GetUserFromContext(r.Context())
		if user == nil {
			http.Error(w, `{"error":"Authentication required"}`, http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// GetUserFromContext retrieves the user from the request context.
func GetUserFromContext(ctx context.Context) *models.User {
	user, ok := ctx.Value(UserContextKey).(*models.User)
	if !ok {
		return nil
	}
	return user
}
