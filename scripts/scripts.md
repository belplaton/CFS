# Scripts

Скрипты для управления инфраструктурой CFS.

## Доступные скрипты

- [`init-db.sql`](init-db.sql) - Инициализация PostgreSQL (создается при первом запуске)
- [`README.md`](README.md) - Полная документация по скриптам

## Быстрый старт

```bash
# Запуск всей инфраструктуры
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Полный сброс (удаление volumes)
docker-compose down -v
```

## Работа с базой данных

### Подключение к PostgreSQL

```bash
# Через docker exec
docker exec -it cfs-postgres psql -U cfs_user -d cfs_database

# Или через connection string
docker exec -it cfs-postgres psql "postgresql://cfs_user:your_secure_password_here@localhost:5432/cfs_database"
```

### Полезные SQL запросы

```sql
-- Показать всех пользователей
SELECT id, email, display_name, created_at FROM users;

-- Показать структуру папок пользователя
SELECT f.path, f.name, COUNT(files.id) as file_count
FROM folders f
LEFT JOIN files ON f.id = files.folder_id
WHERE f.user_id = 'eb4de6d1-4c9a-4ff8-8a68-7d645b1b71d0'
  AND f.is_deleted = FALSE
GROUP BY f.id, f.path, f.name
ORDER BY f.path;

-- Показать последние действия из audit log
SELECT action, resource_type, resource_id, created_at
FROM audit_log
ORDER BY created_at DESC
LIMIT 10;

-- Показать просроченные refresh токены
SELECT user_id, expires_at, is_revoked
FROM refresh_tokens
WHERE expires_at < NOW() AND is_revoked = FALSE;
```

### Сброс базы данных

```bash
# Удалить volume и пересоздать БД
docker-compose down
docker volume rm cfs-postgres-data
docker-compose up -d postgres

# Или удалить все данные через SQL
docker exec -it cfs-postgres psql -U cfs_user -d cfs_database -c "
TRUNCATE TABLE audit_log, file_shares, files, folders, refresh_tokens, users RESTART IDENTITY CASCADE;
"
```

### Бэкап и восстановление

```bash
# Создать бэкап
docker exec cfs-postgres pg_dump -U cfs_user cfs_database > backup_$(date +%Y%m%d).sql

# Восстановить из бэкапа
docker exec -i cfs-postgres psql -U cfs_user -d cfs_database < backup_20260327.sql
```

> **Примечание:** Для production использования рекомендуется создать отдельные скрипты деплоя в `scripts/deploy/`.