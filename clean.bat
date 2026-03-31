@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Cloud File Storage - Полная очистка
echo ============================================
echo.

echo [1/4] Остановка всех сервисов...
docker-compose down
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Не удалось корректно остановить сервисы
)

echo.
echo [2/4] Удаление папки dist...
if exist "frontend\dist" (
    rmdir /s /q frontend\dist
    echo   Папка dist удалена
) else (
    echo   Папка dist не найдена
)

echo.
echo [3/4] Очистка Docker образов проекта...
for /f "tokens=*" %%i in ('docker images --filter "reference=cloudfilestorage-*" -q') do (
    docker rmi -f %%i >nul 2>&1
)
echo   Образы удалены

echo.
echo [4/4] Очистка неиспользуемых Docker ресурсов...
docker system prune -f >nul 2>&1
echo   Кэш Docker очищен

echo.
echo ============================================
echo   Готово! Проект полностью очищен.
echo ============================================
echo.
echo Удалено:
echo   ✓ Контейнеры остановлены
echo   ✓ Папка frontend/dist удалена
echo   ✓ Docker образы проекта удалены
echo   ✓ Docker кэш очищен
echo.
echo Сохранено:
echo   ✓ Исходный код
echo   ✓ Конфигурации
echo   ✓ Файл .env
echo.
echo Для запуска заново: start.bat
echo ============================================
echo.

pause
