@echo off
echo ============================================
echo   Cloud File Storage - Остановка проекта
echo ============================================
echo.

echo Остановка всех сервисов...
docker compose down

echo.
echo Готово! Все сервисы остановлены.
echo.
echo Файлы frontend сохранены в ./frontend/dist
echo Для повторного запуска: start.bat
echo.

pause
