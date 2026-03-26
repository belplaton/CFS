package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// UserSummary представляет информацию о пользователе
type UserSummary struct {
	ID          string `json:"id"`
	Email       string `json:"email"`
	DisplayName string `json:"displayName"`
}

// LoginRequest представляет запрос на вход
type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

// AuthSessionResponse представляет ответ с сессией
type AuthSessionResponse struct {
	AccessToken  string       `json:"accessToken"`
	ExpiresAtUtc time.Time    `json:"expiresAtUtc"`
	User         UserSummary  `json:"user"`
}

// ApiError представляет ошибку API
type ApiError struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}

// HealthResponse представляет ответ health check
type HealthResponse struct {
	Status    string            `json:"status"`
	Timestamp time.Time         `json:"timestamp"`
	Service   string            `json:"service"`
	Version   string            `json:"version"`
	Deps      map[string]string `json:"deps,omitempty"`
}

var (
	// Mock сессии (токен -> пользователь)
	sessions = make(map[string]UserSummary)
)

func main() {
	port := getEnv("AUTH_SERVICE_PORT", "8081")
	host := getEnv("AUTH_SERVICE_HOST", "0.0.0.0")

	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.SetHeader("Content-Type", "application/json"))

	// Health endpoint
	r.Get("/health", healthHandler)

	// Auth endpoints
	r.Route("/api/auth", func(r chi.Router) {
		r.Post("/login", loginHandler)
		r.Get("/me", meHandler)
	})

	addr := host + ":" + port
	println("Auth Service (stub) starting on", addr)

	if err := http.ListenAndServe(addr, r); err != nil {
		println("Error starting server:", err.Error())
		os.Exit(1)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	response := HealthResponse{
		Status:    "ok",
		Timestamp: time.Now().UTC(),
		Service:   "auth-service",
		Version:   "0.1.0-stub",
		Deps: map[string]string{
			"postgres": "mock",
		},
	}
	json.NewEncoder(w).Encode(response)
}

func loginHandler(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ApiError{
			Code:    "auth.invalid_request",
			Message: "Invalid request body",
		})
		return
	}

	if req.Email == "" || req.Password == "" {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ApiError{
			Code:    "auth.invalid_credentials",
			Message: "Email and password are required",
		})
		return
	}

	// Генерируем mock токен
	token := generateToken()
	user := UserSummary{
		ID:          generateUserID(req.Email),
		Email:       req.Email,
		DisplayName: displayNameFromEmail(req.Email),
	}

	// Сохраняем сессию
	sessions[token] = user

	response := AuthSessionResponse{
		AccessToken:  token,
		ExpiresAtUtc: time.Now().UTC().Add(8 * time.Hour),
		User:         user,
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

func meHandler(w http.ResponseWriter, r *http.Request) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(ApiError{
			Code:    "auth.missing_token",
			Message: "Authorization header is required",
		})
		return
	}

	// Извлекаем токен из "Bearer <token>"
	token := authHeader
	if len(authHeader) > 7 && authHeader[:7] == "Bearer " {
		token = authHeader[7:]
	}

	user, exists := sessions[token]
	if !exists {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(ApiError{
			Code:    "auth.invalid_token",
			Message: "Invalid or expired token",
		})
		return
	}

	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(user)
}

// Вспомогательные функции

func generateToken() string {
	bytes := make([]byte, 32)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}

func generateUserID(email string) string {
	// Простая генерация ID из email
	return hex.EncodeToString([]byte(email))[:36]
}

func displayNameFromEmail(email string) string {
	// Извлекаем имя из email
	name := email
	if idx := indexOf(email, '@'); idx != -1 {
		name = email[:idx]
	}
	name = replaceAll(name, ".", " ")
	name = replaceAll(name, "_", " ")
	name = replaceAll(name, "-", " ")
	return toTitleCase(name)
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Простые строковые функции (чтобы избежать импортов)
func indexOf(s string, substr byte) int {
	for i := 0; i < len(s); i++ {
		if s[i] == substr {
			return i
		}
	}
	return -1
}

func replaceAll(s, old, new string) string {
	result := ""
	for i := 0; i < len(s); {
		if i+len(old) <= len(s) && s[i:i+len(old)] == old {
			result += new
			i += len(old)
		} else {
			result += string(s[i])
			i++
		}
	}
	return result
}

func toTitleCase(s string) string {
	if len(s) == 0 {
		return s
	}
	result := ""
	upper := true
	for _, c := range s {
		if upper {
			if c >= 'a' && c <= 'z' {
				c -= 'a' - 'A'
			}
			upper = false
		} else if c == ' ' {
			upper = true
		}
		result += string(c)
	}
	return result
}
