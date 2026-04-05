# 🗺️ Roadmap Cloud File Storage (8 недель)

**Команда:** Ангелов, Беляков, Прибытков  
**Период:** 1 апреля — 27 мая 2026  
**Цель:** MVP с полным функционалом облачного хранилища

---

## 📊 Обзор спринтов

| Спринт | Недели | Фокус | Ключевые результаты |
|--------|--------|-------|---------------------|
| 1 | 1-2 | Инфраструктура + Auth Base | Docker, БД, регистрация, логин |
| 2 | 3-4 | File Service + Frontend Base | Загрузка файлов, файловый менеджер |
| 3 | 5-6 | Продвинутые функции | Корзина, поиск, превью, OAuth |
| 4 | 7-8 | Полировка + Релиз | 2FA, email, тесты, документация |

---

## 📅 Спринт 1: Инфраструктура и базовая аутентификация (Недели 1-2)

### Неделя 1 (1-7 апреля)

#### 🔧 Инфраструктура
- Настроить docker-compose со всеми сервисами
- PostgreSQL (3 экземпляра: auth, file, preview)
- MinIO (хранилище файлов)
- Redis
- Caddy Gateway (reverse proxy)
- Health check endpoints для всех сервисов

#### 👤 Auth Service — Базовая регистрация
- Модель User (SQLAlchemy)
- Модель Session/Token
- Endpoint регистрации (POST /api/auth/register)
- Endpoint логина (POST /api/auth/login)
- JWT токены (access + refresh)
- Хеширование паролей (bcrypt)
- Валидация email и пароля

#### 🎨 Frontend — Базовая структура
- Инициализация React + Vite
- Настройка Tailwind CSS + shadcn/ui
- Роутинг (React Router)
- Страница входа (Login)
- Страница регистрации (Register)
- API клиент (Axios)
- Zustand store для auth state

**Demo к концу недели 1:**
- ✅ Запуск всех сервисов через docker-compose
- ✅ Регистрация нового пользователя
- ✅ Вход и получение JWT токена

---

### Неделя 2 (8-14 апреля)

#### 👤 Auth Service — Восстановление и верификация
- Отправка email (SMTP/Mailtrap)
- Токены верификации email
- Endpoint верификации email (POST /api/auth/verify-email)
- Запрос повторной отправки verification email
- Сброс пароля (запрос + подтверждение)
- Endpoint сброса пароля (POST /api/auth/reset-password)

#### 🎨 Frontend — Auth flow
- Страница верификации email
- Страница запроса сброса пароля
- Страница нового пароля
- Protected routes (AuthGuard)
- Redirect после логина
- Обработка ошибок авторизации
- Refresh token logic

#### 📚 Документация
- Swagger UI для Auth Service
- Описание всех endpoints
- Примеры запросов/ответов

**Demo к концу недели 2:**
- ✅ Полный auth flow: регистрация → верификация → логин
- ✅ Восстановление пароля через email
- ✅ Работающий frontend с формами

---

## 📅 Спринт 2: Файловый сервис и базовый UI (Недели 3-4)

### Неделя 3 (15-21 апреля)

#### 📁 File Service — Базовые операции
- Модель Folder (иерархическая структура)
- Модель File (метаданные)
- MinIO клиент (загрузка/скачивание)
- Endpoint загрузки файла (POST /api/files/upload)
- Endpoint скачивания (GET /api/files/{id}/download)
- Endpoint получения списка файлов
- Endpoint получения метаданных файла
- Валидация типов файлов и размера

#### 🎨 Frontend — Файловый менеджер
- Layout приложения (Sidebar + Main)
- Компонент списка файлов (таблица + сетка)
- Компонент файла (иконка, имя, размер)
- Компонент папки
- Навигация по папкам (хлебные крошки)
- Загрузка файлов (drag & drop)
- Индикатор прогресса загрузки

**Demo к концу недели 3:**
- ✅ Загрузка файла через API
- ✅ Просмотр списка файлов в UI
- ✅ Скачивание файла

---

### Неделя 4 (22-28 апреля)

#### 📁 File Service — Управление структурой
- Создание папки (POST /api/folders)
- Переименование папки/файла (PATCH)
- Перемещение файла в папку (POST /api/files/{id}/move)
- Удаление файла (мягкое) (DELETE /api/files/{id})
- Удаление папки (мягкое)
- Квоты пользователя (проверка перед загрузкой)
- Audit logs (опционально)

#### 🎨 Frontend — Управление файлами
- Контекстное меню файла
- Диалог создания папки
- Диалог переименования
- Перемещение файлов (drag & drop в папку)
- Удаление файлов (с подтверждением)
- Поиск по имени файла
- Сортировка (по имени, дате, размеру)

#### 🔐 Безопасность
- Проверка прав доступа к файлам
- Валидация owner_id
- Rate limiting на загрузку

**Demo к концу недели 4:**
- ✅ Полное управление файлами и папками
- ✅ Drag & drop загрузка и перемещение
- ✅ Поиск и сортировка файлов

---

## 📅 Спринт 3: Продвинутые функции (Недели 5-6)

### Неделя 5 (29 апреля — 5 мая)

#### 🗑️ Корзина (Trash)
- Модель soft delete (deleted_at)
- Endpoint перемещения в корзину
- Endpoint восстановления из корзины
- Endpoint безвозвратного удаления
- Endpoint очистки корзины
- Cron job для автоудаления (30 дней)
- Endpoint списка файлов в корзине

#### 🎨 Frontend — Корзина
- Страница корзины
- Восстановление файлов
- Безвозвратное удаление
- Очистка корзины
- Индикатор "файл в корзине"

#### 🔍 Поиск
- Полнотекстовый поиск по имени файлов
- Поиск по содержимому папок
- Фильтрация по типу файла
- Endpoint поиска (GET /api/search?q=...)

**Demo к концу недели 5:**
- ✅ Корзина с восстановлением и удалением
- ✅ Поиск файлов по имени

---

### Неделя 6 (6-12 мая)

#### 🔐 OAuth Google
- Настройка Google OAuth Console
- Endpoint авторизации (GET /api/auth/oauth/google)
- Callback endpoint (GET /api/auth/oauth/google/callback)
- Связывание Google аккаунта с существующим user
- Создание нового user через OAuth
- Кнопка "Войти через Google" на frontend

#### 🖼️ Preview Service — Изображения
- Модель PreviewCache
- Генерация превью изображений
- Хранение превью в Redis
- Endpoint получения превью (GET /api/preview/{id})
- Endpoint получения thumbnail
- Поддержка форматов: JPEG, PNG, GIF, WebP, SVG

#### 🎨 Frontend — Preview и OAuth
- Кнопка входа через Google
- Предпросмотр изображений (modal)
- Галерея изображений
- Lazy loading превью

**Demo к концу недели 6:**
- ✅ Вход через Google OAuth
- ✅ Превью изображений в файловом менеджере
- ✅ Корзина полностью функциональна

---

## 📅 Спринт 4: Полировка и релиз (Недели 7-8)

### Неделя 7 (13-19 мая)

#### 🔐 2FA (TOTP)
- Генерация TOTP секрета
- Endpoint получения QR-кода
- Endpoint включения 2FA
- Endpoint отключения 2FA
- Верификация TOTP кода при логине
- Backup коды для восстановления

#### 📁 Preview Service — Документы
- Превью PDF (конвертация в изображения)
- Превью документов (docx, xlsx → PDF/images)
- Превью текстовых файлов
- Хранение превью в Redis

#### 🎨 Frontend — 2FA и превью
- Страница настройки 2FA
- Ввод TOTP кода при логине
- Просмотр PDF в браузере
- Просмотр документов

#### 📊 Статистика и квоты
- Endpoint статистики использования (GET /api/quota)
- Визуализация квоты в UI
- Прогресс-бар использования места

**Demo к концу недели 7:**
- ✅ 2FA работает при логине
- ✅ Просмотр PDF и документов
- ✅ Индикатор квоты хранилища

---

### Неделя 8 (20-27 мая)

#### 🧪 Тестирование
- Unit тесты для Auth Service
- Unit тесты для File Service
- Integration тесты API
- E2E тесты критических сценариев
- Load testing (опционально)

#### 🐛 Исправление багов
- Сбор и приоритизация багов
- Исправление критических багов
- Исправление UX проблем
- Оптимизация производительности

#### 📚 Документация
- README с инструкцией по запуску
- API документация (Swagger)
- ARCHITECTURE.md
- Инструкция для разработчиков
- Changelog

#### 🚀 Подготовка к релизу
- Финальное тестирование
- Проверка безопасности
- Мониторинг и логирование

**Demo к концу недели 8:**
- ✅ Все тесты проходят
- ✅ Документация полная
- ✅ Готово к production

---

## 📋 Распределение задач по разработчикам

### 👤 Ангелов (Backend + DB)

| Неделя | Задачи |
|--------|--------|
| 1-2 | Auth Service: регистрация, логин, JWT, email |
| 3-4 | Rate limiting, security hardening |
| 5-6 | OAuth Google интеграция |
| 7-8 | 2FA (TOTP), финальное тестирование |

### 👤 Беляков (Frontend)

| Неделя | Задачи |
|--------|--------|
| 1-2 | Frontend: auth страницы, роутинг, store |
| 3-4 | File Service + файловый менеджер UI |
| 5-6 | Корзина + поиск |
| 7-8 | Квоты, статистика, оптимизация UI |

### 👤 Прибытков (Backend + Infrastructure(MinIO, Redis))

| Неделя | Задачи |
|--------|--------|
| 1-2 | Docker Compose, БД, MinIO, Caddy, Redis |
| 3-4 | MinIO интеграция, загрузка файлов |
| 5-6 | Preview Service (изображения) + Redis кэш |
| 7-8 | Preview (документы), мониторинг |

---

## 🎯 Критерии готовности MVP

### Функциональные
- Регистрация/вход (email + Google OAuth)
- 2FA (TOTP)
- Верификация email
- Восстановление пароля
- Загрузка/скачивание файлов (до 100 МБ)
- Управление папками (создание, переименование, перемещение)
- Удаление файлов (корзина 30 дней)
- Поиск по имени файлов
- Предпросмотр (изображения, PDF, документы)
- Квота 5 ГБ (бесплатно)

### Нефункциональные
- Все сервисы в Docker контейнерах
- API документация (Swagger)
- Unit тесты > 70% coverage
- CORS настроен корректно
- Rate limiting на auth endpoints
- Логи
- README и документация

---

## 🚦 Вехи (Milestones)

| Веха | Дата | Критерий |
|------|------|----------|
| M1: Infrastructure Ready | 7 апреля | Все сервисы запускаются |
| M2: Auth Complete | 14 апреля | Полный auth flow работает |
| M3: File Management | 28 апреля | Файлы + папки + UI |
| M4: Advanced Features | 12 мая | Корзина, поиск, OAuth, preview |
| M5: Security Complete | 19 мая | 2FA, email, документы |
| **M6: MVP Release** | **27 мая** | **Готово к production** |

---

## 🏗️ C3 Diagrams — Component Diagrams (Mermaid)

### C3.1 — Auth Service (Components)

```mermaid
graph TB
    subgraph Auth_Service["Auth Service (FastAPI)"]
        subgraph API_Layer["API Routes Layer"]
            Register["POST /register"]
            Login["POST /login"]
            OAuth["GET/POST /oauth/google"]
            Verify["POST /verify-email"]
            Reset["POST /reset-password"]
        end

        subgraph Service_Layer["Service Layer"]
            AuthService["AuthService\n• register()\n• login()\n• validate()"]
            OAuthSvc["OAuthService\n• google_auth()\n• callback()\n• link_account()"]
            EmailSvc["EmailService\n• send_verify()\n• send_reset()"]
            TokenSvc["TokenService\n• create_jwt()\n• refresh()\n• validate()\n• revoke()"]
        end

        subgraph DAL["Data Access Layer (Repositories)"]
            UserRepo["User Repository\n• create()\n• find_by_id()\n• find_by_email()\n• update()"]
            SessionRepo["Session Repository\n• create()\n• find_by_user()\n• update()\n• delete()"]
        end
    end

    PostgreSQL_Auth[("PostgreSQL\n(auth:5433)\n• users\n• sessions\n• verif_tokens")]
    Redis_Auth[("Redis\n(cache:6379)\n• rate_limit\n• tokens\n• login_attempts")]

    Register --> AuthService
    Login --> AuthService
    OAuth --> OAuthSvc
    Verify --> EmailSvc
    Reset --> EmailSvc

    AuthService --> UserRepo
    AuthService --> TokenSvc
    OAuthSvc --> UserRepo
    EmailSvc --> TokenSvc

    UserRepo --> PostgreSQL_Auth
    SessionRepo --> PostgreSQL_Auth
    TokenSvc --> Redis_Auth
    AuthService -. rate limit .-> Redis_Auth
```

---

### C3.2 — File Service (Components)

```mermaid
graph TB
    subgraph File_Service["File Service (FastAPI)"]
        subgraph API_Layer["API Routes Layer"]
            FilesAPI["CRUD /files\n• upload\n• download\n• delete\n• get_meta"]
            FoldersAPI["CRUD /folders\n• create\n• rename\n• move\n• delete"]
            SearchAPI["GET /search\n• by_name\n• by_type\n• filters\n• sort"]
            TrashAPI["GET/POST/DELETE /trash\n• list\n• restore\n• delete_permanent"]
            QuotaAPI["GET /quota\n• check\n• get_usage"]
        end

        subgraph Service_Layer["Service Layer"]
            FileSvc["FileService\n• upload()\n• download()\n• delete()\n• get_meta()"]
            FolderSvc["FolderService\n• create()\n• rename()\n• move()\n• delete()"]
            SearchSvc["SearchService\n• by_name()\n• by_type()\n• filters()\n• sort()"]
            QuotaSvc["QuotaService\n• check()\n• update_usage()\n• get_usage()\n• validate()"]
        end

        subgraph DAL["Data Access Layer (Repositories)"]
            FileRepo["File Repository\n• create()\n• find_by_*()\n• update()\n• soft_delete()"]
            FolderRepo["Folder Repository\n• create()\n• find_by_user()\n• update_path()\n• cascade_del()"]
        end
    end

    PostgreSQL_File[("PostgreSQL\n(file:5434)\n• files\n• folders\n• audit_logs")]
    MinIO[("MinIO\n(storage:9000)\n• {user_id}/files/\n• {user_id}/trash/\n• {user_id}/shared/")]

    FilesAPI --> FileSvc
    FoldersAPI --> FolderSvc
    SearchAPI --> SearchSvc
    TrashAPI --> FileSvc
    QuotaAPI --> QuotaSvc

    FileSvc --> FileRepo
    FileSvc --> QuotaSvc
    FolderSvc --> FolderRepo
    SearchSvc --> FileRepo

    FileRepo --> PostgreSQL_File
    FolderRepo --> PostgreSQL_File
    FileSvc -. store/retrieve .-> MinIO
```

---

### C3.3 — Preview Service (Components)

```mermaid
graph TB
    subgraph Preview_Service["Preview Service (FastAPI)"]
        subgraph API_Layer["API Routes Layer"]
            PreviewAPI["GET /preview/{file_id}\n• Получить или сгенерировать"]
            PreviewDL["GET /preview/{file_id}/download\n• Скачать превью"]
            PreviewDel["DELETE /preview/{file_id}\n• Удалить из кэша"]
        end

        subgraph Service_Layer["Service Layer"]
            PreviewMgr["PreviewManager\n• get_or_generate()\n• invalidate()\n• cache_control()"]
            ImageSvc["ImageService\n• resize()\n• optimize()\n• format()"]
            PDFSvc["PDFService\n• convert()\n• render()\n• extract_pages()"]
            DocSvc["DocumentService\n• libreoffice_convert()\n• to_images()\n• preview()"]
        end

        subgraph Processing["Document Processing Layer"]
            LibreOffice["LibreOffice (headless)\n• .docx → PDF\n• .xlsx → PDF\n• .pptx → PDF"]
            PDF2Image["pdf2image\n• PDF → JPEG/PNG"]
            Pillow["Pillow\n• JPEG, PNG, GIF\n• WebP, SVG, BMP"]
        end
    end

    PostgreSQL_Preview[("PostgreSQL\n(preview:5435)\n• preview_cache\n• TTL metadata\n• created_at")]
    Redis_Preview[("Redis\n(cache:6379)\n• preview_cache\n• binary data\n• expires_at")]
    MinIO_Preview[("MinIO\n(storage:9000)\n• {user_id}/preview/{id}.jpg\n• {user_id}/preview/{id}.pdf\n• {user_id}/preview/{id}_thumb.jpg")]

    PreviewAPI --> PreviewMgr
    PreviewDL --> PreviewMgr
    PreviewDel --> PreviewMgr

    PreviewMgr --> ImageSvc
    PreviewMgr --> PDFSvc
    PreviewMgr --> DocSvc

    ImageSvc --> Pillow
    PDFSvc --> PDF2Image
    DocSvc --> LibreOffice
    LibreOffice --> PDF2Image

    PreviewMgr --> PostgreSQL_Preview
    PreviewMgr --> Redis_Preview
    PreviewMgr -. store preview .-> MinIO_Preview
```

---

### C3.4 — Frontend (Components)

```mermaid
graph TB
    subgraph Frontend["React Frontend (SPA)"]
        subgraph Pages["Pages Layer"]
            LoginPage["Login Page\n/login"]
            RegisterPage["Register Page\n/register"]
            DashboardPage["Dashboard (Files)\n/files"]
            TrashPage["Trash Page\n/trash"]
        end

        subgraph Components["Components Layer"]
            FileManager["FileManager\n(grid/list view)"]
            FileCard["FileCard\n(file item)"]
            PreviewModal["Preview Modal\n(img/pdf viewer)"]
            UploadWidget["UploadWidget\n(drag & drop)"]
            Sidebar["Sidebar\n(navigation)"]
            Breadcrumb["Breadcrumb\n(path)"]
            SearchBar["SearchBar\n(filter)"]
            QuotaBar["QuotaBar\n(progress)"]
        end

        subgraph StateMgmt["State Management (Zustand)"]
            AuthStore["authStore\n• user\n• token\n• isAuth\n• isLoading\n• error"]
            FileStore["fileStore\n• files[]\n• folders[]\n• currentDir\n• loading\n• selected[]"]
            UIStore["uiStore\n• theme (dark/light)\n• modals[]\n• toasts[]\n• searchQuery\n• breadcrumbs[]"]
        end

        subgraph APIClient["API Client Layer (Axios)"]
            AuthAPI["authApi\n• login()\n• register()\n• verify()\n• oauth()\n• resetPwd()"]
            FileAPI["fileApi\n• upload()\n• download()\n• delete()\n• search()\n• move()"]
            PreviewAPI_FE["previewApi\n• getPreview()\n• downloadPreview()\n• invalidateCache()"]
        end
    end

    CaddyGateway["Caddy Gateway\n(localhost:8080)"]

    LoginPage --> AuthStore
    RegisterPage --> AuthStore
    DashboardPage --> FileStore
    TrashPage --> FileStore

    FileManager --> FileStore
    FileCard --> FileStore
    PreviewModal --> UIStore
    UploadWidget --> FileStore
    Sidebar --> UIStore
    Breadcrumb --> UIStore
    SearchBar --> UIStore
    QuotaBar --> UIStore

    AuthStore --> AuthAPI
    FileStore --> FileAPI
    UIStore --> PreviewAPI_FE

    AuthAPI -. HTTPS .-> CaddyGateway
    FileAPI -. HTTPS .-> CaddyGateway
    PreviewAPI_FE -. HTTPS .-> CaddyGateway
```

---

### C3.5 — System Context (Общая архитектура)

```mermaid
graph TB
    User["👤 User\n(Browser)"]
    Google["🔐 Google\nOAuth Provider"]
    Email["📧 Email Server\n(Mailtrap/SMTP)"]

    subgraph System["Cloud File Storage System"]
        Caddy["Caddy Gateway\n(reverse proxy :8080)\n\n/api/auth/* → Auth Service\n/api/files/* → File Service\n/api/preview/* → Preview Service\n/* → Frontend (React SPA)"]

        subgraph Services["Backend Services"]
            AuthService["Auth Service\n(FastAPI)"]
            FileService["File Service\n(FastAPI)"]
            PreviewService["Preview Service\n(FastAPI)"]
        end

        subgraph Databases["Databases"]
            PG_Auth[("PostgreSQL\n(auth DB)")]
            PG_File[("PostgreSQL\n(file DB)")]
            PG_Preview[("PostgreSQL\n(preview DB)")]
        end

        Storage["MinIO\n(files storage)"]
        Redis_Preview["Redis\n(preview cache)"]
    end

    User -. HTTPS .-> Caddy
    Google -. OAuth2 .-> Caddy
    Email -. SMTP .-> Caddy

    Caddy --> AuthService
    Caddy --> FileService
    Caddy --> PreviewService

    AuthService --> PG_Auth
    FileService --> PG_File
    PreviewService --> PG_Preview
    PreviewService --> Redis_Preview

    FileService --> Storage
    PreviewService --> Storage
```

---

## 📐 C4 Diagrams — Code Level (Mermaid Sequence Diagrams)

### C4.1 — Регистрация пользователя (POST /api/auth/register)

```mermaid
sequenceDiagram
    participant Client
    participant Router as API Router
    participant AuthService
    participant UserRepo as User Repository
    participant PwdUtils as Password Utils
    participant DB as PostgreSQL

    Client->>Router: POST /register {email, password}
    Router->>AuthService: validate input (email format, password strength)

    AuthService->>PwdUtils: hash_password (bcrypt, cost=12)
    PwdUtils-->>AuthService: hashed_password

    AuthService->>DB: INSERT INTO users (email, hashed_password, is_verified, created_at)
    DB-->>AuthService: user (id, email, created_at)

    AuthService->>DB: INSERT INTO verification_tokens (user_id, token, type, expires_at)
    Note over AuthService: Generate JWT token (24h expiry)

    par Send email asynchronously
        AuthService->>Email: send_verification_email via SMTP/Mailtrap
        Note over AuthService: Non-blocking, doesn't wait for response
    end

    AuthService-->>Router: 201 Created {user_id, email, message}
    Router-->>Client: 201 Created {"user_id": "uuid", "email": "user@example.com", "message": "Check your email"}
```

---

### C4.2 — Логин с JWT (POST /api/auth/login)

```mermaid
sequenceDiagram
    participant Client
    participant Router as API Router
    participant AuthService
    participant UserRepo as User Repository
    participant JWT as JWT Utils
    participant DB as PostgreSQL
    participant Redis

    Client->>Router: POST /login {email, password}
    Router->>AuthService: process login

    AuthService->>Redis: check_rate_limit (GET rate_limit:{ip})
    Redis-->>AuthService: attempts count

    alt attempts >= max
        AuthService->>Redis: increment_rate_limit (INCR rate_limit:{ip})
        AuthService-->>Router: 429 Too Many Requests
        Router-->>Client: 429 {"error": "Too many attempts"}
    else attempts < max AND user found
        AuthService->>DB: SELECT * FROM users WHERE email = ?
        DB-->>AuthService: user (if exists)

        alt user not found or invalid password
            AuthService->>PwdUtils: verify_password (bcrypt.compare)
            PwdUtils-->>AuthService: valid: false
            AuthService->>Redis: increment_rate_limit (INCR rate_limit:{ip})
            AuthService-->>Router: 401 Unauthorized
            Router-->>Client: 401 {"error": "Invalid credentials"}
        else user found AND password valid
            AuthService->>JWT: generate_tokens (access: 15m, refresh: 7d)
            JWT-->>AuthService: {access_token, refresh_token}

            AuthService->>DB: INSERT INTO sessions (user_id, refresh_token, expires_at)
            AuthService->>Redis: reset_rate_limit (DEL rate_limit:{ip})

            AuthService-->>Router: 200 OK {access_token, refresh_token, user}
            Router-->>Client: 200 OK {"access_token": "eyJ...", "refresh_token": "eyJ...", "user": {id, email}}
        end
    end
```

---

### C4.3 — Загрузка файла (POST /api/files/upload)

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as Caddy Gateway
    participant FileSvc as File Service
    participant AuthMW as Auth Middleware
    participant QuotaSvc as Quota Service
    participant MinIO
    participant DB as PostgreSQL

    Client->>Gateway: POST /files/upload (multipart/form-data)
    Gateway->>FileSvc: forward request + headers

    FileSvc->>AuthMW: validate_token (JWT from Auth)
    AuthMW-->>FileSvc: user_id, email

    FileSvc->>QuotaSvc: check_quota (user_id, file_size)
    QuotaSvc->>DB: SELECT SUM(size) FROM files WHERE user_id = ?
    DB-->>QuotaSvc: current_usage
    QuotaSvc-->>FileSvc: quota_ok: true/false

    alt quota exceeded
        FileSvc-->>Gateway: 413 Payload Too Large
        Gateway-->>Client: 413 {"error": "Storage quota exceeded"}
    else quota OK
        FileSvc->>MinIO: upload_to_minio {user_id}/files/{uuid}.{ext}
        MinIO-->>FileSvc: minio_object_id

        FileSvc->>DB: INSERT INTO files (user_id, folder_id, name, size, mime_type, minio_object_id)
        DB-->>FileSvc: file_id

        FileSvc-->>Gateway: 201 Created {file_id, name, size, mime_type}
        Gateway-->>Client: 201 Created {"file_id": "uuid", "name": "document.pdf", "size": 1048576, "mime_type": "application/pdf"}
    end
```

---

### C4.4 — Генерация превью (GET /api/preview/{file_id})

```mermaid
sequenceDiagram
    participant Client
    participant PreviewSvc as Preview Service
    participant Redis as Redis Cache
    participant MinIO
    participant ImageLib as Pillow/pdf2image
    participant LibreOffice

    Client->>PreviewSvc: GET /preview/{file_id}
    PreviewSvc->>Redis: check_cache {file_id, preview_type}
    Redis-->>PreviewSvc: cache_hit: true/false

    alt cache HIT
        PreviewSvc-->>Client: 200 OK {preview_url, type}
    else cache MISS
        PreviewSvc->>PreviewSvc: get_file_metadata (from File Service via REST)
        Note over PreviewSvc: {minio_object_id, mime_type}

        PreviewSvc->>MinIO: download_from_minio {user_id}/files/{file_id}.{ext}
        MinIO-->>PreviewSvc: file_bytes (max 50MB)

        PreviewSvc->>PreviewSvc: detect_file_type (image/pdf/doc)

        alt image file
            PreviewSvc->>ImageLib: Image.open() → resize → optimize
            ImageLib-->>PreviewSvc: preview_image (JPEG/WebP)
        else PDF file
            PreviewSvc->>ImageLib: pdf2image.convert_from_path() (1st page → JPEG)
            ImageLib-->>PreviewSvc: preview_image
        else document file
            PreviewSvc->>LibreOffice: libreoffice --headless --convert-to pdf
            LibreOffice->>ImageLib: pdf2image on converted PDF
            ImageLib-->>PreviewSvc: preview_image
        end

        PreviewSvc->>MinIO: upload_preview_to_minio {user_id}/preview/{file_id}.jpg
        MinIO-->>PreviewSvc: preview_minio_id

        PreviewSvc->>Redis: cache_preview {file_id, preview_type, minio_id, expires_at}
        Redis-->>PreviewSvc: cached

        PreviewSvc-->>Client: 200 OK {"preview_url": "/api/preview/{id}/download", "type": "image/jpeg", "expires_at": "2026-05-..."}
    end
```

---

### C4.5 — Перемещение в корзину и восстановление

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as Caddy Gateway
    participant FileSvc as File Service
    participant TrashSvc as Trash Service
    participant DB as PostgreSQL

    Note over Client, DB: === DELETE (Soft Delete) ===
    Client->>Gateway: DELETE /files/{id}
    Gateway->>FileSvc: forward request

    FileSvc->>DB: SELECT * FROM files WHERE id = ? AND user_id = ?
    DB-->>FileSvc: file (exists)

    alt not found or not owner
        FileSvc-->>Gateway: 404 Not Found / 403 Forbidden
        Gateway-->>Client: 404/403
    else found AND owner
        FileSvc->>DB: UPDATE files SET deleted_at = NOW() WHERE id = ?
        DB-->>FileSvc: success

        FileSvc-->>Gateway: 200 OK
        Gateway-->>Client: 200 {"message": "Moved to trash"}
    end

    Note over Client, DB: === LIST TRASH ===
    Client->>Gateway: GET /trash
    Gateway->>TrashSvc: forward request

    TrashSvc->>DB: SELECT * FROM files WHERE user_id = ? AND deleted_at IS NOT NULL
    DB-->>TrashSvc: deleted_files[]
    TrashSvc-->>Gateway: 200 OK {files: [...]}
    Gateway-->>Client: 200 OK {files: [...]}

    Note over Client, DB: === RESTORE FROM TRASH ===
    Client->>Gateway: POST /trash/{id}/restore
    Gateway->>TrashSvc: forward request

    TrashSvc->>DB: UPDATE files SET deleted_at = NULL WHERE id = ?
    DB-->>TrashSvc: success

    TrashSvc-->>Gateway: 200 OK
    Gateway-->>Client: 200 {"message": "File restored"}
```

---

### C4.6 — Cron job: Автоматическая очистка корзины (30 дней)

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant FileSvc as File Service
    participant DB as PostgreSQL
    participant MinIO

    Scheduler->>FileSvc: trigger_cleanup (Every day 02:00)

    FileSvc->>DB: SELECT * FROM files WHERE deleted_at < NOW() - interval '30 days'
    DB-->>FileSvc: expired_files[]

    loop for each expired file
        FileSvc->>DB: DELETE FROM files WHERE id = ?
        Note over DB: Soft-delete → permanent delete
    end

    DB-->>FileSvc: deleted_count

    loop for each expired file
        FileSvc->>MinIO: delete_object(minio_object_id)
        MinIO-->>FileSvc: deleted
    end

    FileSvc-->>Scheduler: cleanup_complete {deleted: N files}
    Note over Scheduler: Log result: "Cleaned up N expired files"
```

---

### C4.7 — Поиск файлов (GET /api/search?q=query)

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as Caddy Gateway
    participant FileSvc as File Service
    participant SearchSvc as Search Service
    participant DB as PostgreSQL

    Client->>Gateway: GET /search?q=report
    Gateway->>FileSvc: forward request

    FileSvc->>SearchSvc: parse_query (q="report", type=..., folder=...)

    SearchSvc->>DB: SELECT * FROM files WHERE user_id = ? AND deleted_at IS NULL AND (name ILIKE '%report%' OR name % 'report') ORDER BY similarity(name, 'report') DESC LIMIT 50
    Note over DB: Using pg_trigram extension for fuzzy search

    DB-->>SearchSvc: results[]

    SearchSvc->>SearchSvc: enrich_results (folder names, preview URLs)

    SearchSvc-->>FileSvc: enriched_results[]
    FileSvc-->>Gateway: 200 OK {results, total}
    Gateway-->>Client: 200 OK {"results": [{"id": "uuid", "name": "report.pdf", "type": "file", "folder": "/Documents", "size": 2048576, "preview_url": "..."}], "total": 5}
```
