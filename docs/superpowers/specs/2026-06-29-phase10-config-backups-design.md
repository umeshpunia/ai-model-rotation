# Design Specification: Phase 10 Configuration, Profiles & Backups

## 1. Goal
Provide full REST API endpoints for system configuration settings and backups. This includes supporting Settings Profiles (Development, Production, Testing), backup generation/restores, and hot-reloading configurations.

## 2. Requirements & Scope
- **Settings CRUD & Profiles**:
  * settings are queryable and editable per profile (`default`, `development`, `production`, `testing`).
  * Add configuration import/export endpoints via standard JSON payloads.
- **Backup System**:
  * `GET /api/v1/backups`: Lists existing backups.
  * `POST /api/v1/backups`: Creates a manual backup (copies and compresses the current database file).
  * `DELETE /api/v1/backups/{id}`: Deletes a backup record and removes the file from disk.
  * `POST /api/v1/backups/{id}/restore`: Restores the application database from a backup file (temporarily closes DB connections, replaces the file, and re-initializes engine).
- **Hot-Reload**:
  * Trigger dynamic configuration reloads on settings changes (re-evaluating logger settings or background jobs schedule intervals).

## 3. Database Schema: Backups Table
Using the `Backup` entity:
```python
class Backup(IDMixin, TimestampMixin, table=True):
    __tablename__ = "backups"
    filename: str
    filepath: str
    size_bytes: int
    is_automatic: bool
    status: str  # SUCCESS, FAILED
```
