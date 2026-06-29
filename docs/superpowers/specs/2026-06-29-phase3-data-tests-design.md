# Design Specification: Phase 3 Data Layer Verification & Testing

## 1. Goal
Validate that all Phase 3 elements (SQLModel ORM models, relationships, CRUD repositories, Pydantic schemas, and Alembic migrations) are fully verified and correctly implemented, ensuring a production-ready, reliable, and error-free database layer.

## 2. Requirements & Scope
- **ORM Table Creation**: Verify that the database schema compiles and maps correctly, and that Alembic migrations run cleanly on a test SQLite database.
- **Entity and Relationship Validation**: Verify:
  - Provider model configuration, priority, and enums.
  - API key model properties, priority, status, and encryption hooks.
  - Cascading deletes (e.g., deleting a provider removes its models and API keys).
  - User model properties, hashed password verification, and roles.
- **Repository Pattern CRUD**:
  - Verify that the generic `BaseRepository` supports standard CRUD: add, create, update, get, list, paginate, and delete.
  - Verify that specific repositories (e.g., `ProviderRepository`, `ApiKeyRepository`, `UserRepository`) support custom domain operations.
- **Schema Validation**: Verify that Pydantic schemas (`ProviderCreate`, `ApiKeyCreate`, `UserCreate`, etc.) apply correct validations and serialize ORM entities correctly.

## 3. Design Details

### A. Model Verification (`test_models.py`)
- Setup an in-memory SQLite database via the transactional `session_scope` fixture.
- Test insertion and properties of each ORM entity under `app/domain/entities/`.
- Test table relations:
  - Assert that adding a `Model` or `ApiKey` to `Provider.models` or `Provider.api_keys` updates the relationship correctly.
  - Assert that deleting the parent `Provider` automatically cascade-deletes children (no orphans left in the database).

### B. Repository CRUD Verification (`test_repositories.py`)
- Test standard repository methods on a model (like `Provider` or `User`):
  - `add()`, `get()`, `get_or_404()`, `update()`, `delete()`.
  - `list()` with filters/limit/offset.
  - `paginate()` to return paginated lists and count.
  - `count()` to return correct matching records.
- Test specific repository overrides:
  - `ApiKeyRepository` to retrieve active keys.
  - `UserRepository` to retrieve a user by email/username.

### C. DTO Schema Validation (`test_schemas.py`)
- Verify that initializing schemas with invalid inputs raises `ValidationError`:
  - `UserCreate` with invalid email format.
  - Fields with incorrect types or values out of range.
- Verify serialization of database instances using `.model_validate(entity)`.

### D. Alembic Migration Sanity Check
- Verify the Alembic migration scripts execute correctly against a test database instance without syntax or migration execution errors.

## 4. Verification Plan
Run `pytest` to execute the database models, repositories, and schema validation tests:
```bash
.venv\Scripts\pytest tests/ -v
```
Assert that all 12 existing tests + new Phase 3 tests pass successfully.
