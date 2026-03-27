# Scripts Documentation

## Database Initialization

### `init-db.sql`

PostgreSQL database initialization script that runs automatically when the PostgreSQL container starts for the first time.

**What it creates:**

1. **Tables:**
   - `users` - User accounts with authentication data
   - `refresh_tokens` - JWT refresh token storage
   - `folders` - Hierarchical folder structure
   - `files` - File metadata with MinIO references
   - `file_shares` - File sharing permissions
   - `audit_log` - User action audit trail

2. **Indexes:**
   - Optimized lookups for email, tokens, folder/file hierarchies
   - Soft-delete filtering indexes
   - Timestamp-based query indexes

3. **Triggers:**
   - Auto-update `updated_at` timestamps
   - Auto-set `deleted_at` on soft delete

4. **Seed Data:**
   - Demo user: `user@cfs.local` / `demo123`
   - Default root folder
   - Sample folders: Design, Documents, Projects

**Schema Features:**

- UUID primary keys for all entities
- Soft delete support (`is_deleted`, `deleted_at`)
- Unique constraints per user/folder hierarchy
- Foreign key constraints with CASCADE delete
- JSONB support for audit log details
- INET type for IP address storage

**Database Diagram:**

```
┌─────────────────┐     ┌─────────────────┐
│     users       │     │  refresh_tokens │
├─────────────────┤     ├─────────────────┤
│ id (UUID)       │◄────│ user_id (UUID)  │
│ email           │     │ token           │
│ password_hash   │     │ expires_at      │
│ display_name    │     │ is_revoked      │
│ created_at      │     └─────────────────┘
│ updated_at      │
└─────────────────┘
         │
         │         ┌─────────────────┐
         └────────►│    folders      │
                   ├─────────────────┤
         ┌────────►│ id (UUID)       │
         │         │ user_id (UUID)  │
         │         │ parent_id (UUID)│──┐
         │         │ name            │  │
         │         │ path            │  │ (self-referencing
         │         │ created_at      │  │  for hierarchy)
         │         │ updated_at      │  │
         │         │ is_deleted      │  │
         │         └─────────────────┘  │
         │                              │
         │         ┌─────────────────┐  │
         │         │     files       │  │
         │         ├─────────────────┤  │
         │         │ id (UUID)       │  │
         │         │ user_id (UUID)  │  │
         │         │ folder_id (UUID)│──┘
         │         │ name            │
         │         │ storage_key     │──► MinIO Object
         │         │ size_bytes      │
         │         │ version         │
         │         │ is_deleted      │
         │         └─────────────────┘
         │
         │         ┌─────────────────┐
         └────────►│   file_shares   │
                   ├─────────────────┤
                   │ file_id (UUID)  │
                   │ owner_id (UUID) │
                   │ shared_with_id  │
                   │ permission      │
                   │ expires_at      │
                   └─────────────────┘
```

## Usage

The script is automatically mounted to PostgreSQL container via docker-compose:

```yaml
volumes:
  - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql:ro
```

**Important:** The script only runs on **first initialization** of the PostgreSQL database. If you need to re-run it:

1. Stop all containers: `docker-compose down`
2. Remove PostgreSQL volume: `docker volume rm cfs-postgres-data`
3. Start again: `docker-compose up -d`

## Manual Execution

To run the script manually on an existing database:

```bash
docker exec -i cfs-postgres psql -U cfs_user -d cfs_database < scripts/init-db.sql
```

Or connect with your preferred PostgreSQL client and execute the script.

## Demo Credentials

After initialization, you can login with:

- **Email:** `user@cfs.local`
- **Password:** `demo123`

**⚠️ WARNING:** This is a demo account for development only. Remove or change the password in production!

## Migration Strategy

For production deployments:

1. **Remove seed data** section from `init-db.sql`
2. Create separate migration scripts in `scripts/migrations/`
3. Use Alembic (for Python service) or golang-migrate (for Go services)
4. Never use demo credentials in production

## Backup & Restore

**Backup:**
```bash
docker exec cfs-postgres pg_dump -U cfs_user cfs_database > backup.sql
```

**Restore:**
```bash
docker exec -i cfs-postgres psql -U cfs_user -d cfs_database < backup.sql
```
