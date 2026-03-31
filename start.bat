@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Cloud File Storage - Запуск проекта
echo ============================================
echo.

echo [1/2] Сборка и запуск сервисов...
echo.

:: Build and start all services
docker compose up -d --build
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Не удалось запустить сервисы!
    pause
    exit /b 1
)

echo.
echo [2/2] Ожидание запуска frontend (30 секунд)...
timeout /t 30 /nobreak >nul

echo.
echo ============================================
echo   Готово! Все сервисы запущены.
echo ============================================
echo.
echo   Frontend:       http://localhost:8080
echo   Auth DB:        localhost:5433
echo   File DB:        localhost:5434
echo   Preview DB:     localhost:5435
echo   MinIO Console:  http://localhost:9001
echo   Redis:          localhost:6379
echo.
echo   API Docs:
echo     Auth:    http://localhost:8080/api/auth/docs
echo     File:    http://localhost:8080/api/files/docs
echo     Preview: http://localhost:8080/api/preview/docs
echo.
echo   Для остановки:  docker compose down
echo ============================================
echo.

pause
