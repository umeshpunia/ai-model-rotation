# Contributing to AI Gateway Pro

Thank you for your interest in contributing to **AI Gateway Pro**! We welcome bug reports, feature requests, documentation improvements, and pull requests.

Following these guidelines helps ensure a smooth contribution process for everyone.

---

## 🚀 How to Get Started

### 1. Find or File an Issue
- Search the [Issue Tracker](https://github.com/umeshpunia/ai-model-rotation/issues) for active tasks or bugs.
- If you find a bug or have a feature idea, open a new issue describing it in detail.

### 2. Fork and Clone
Fork the repository to your own GitHub account, then clone it locally:
```bash
git clone https://github.com/your-username/ai-model-rotation.git
cd ai-model-rotation
```

### 3. Set Up Development Environment

#### Backend (Python)
- Navigate to the `backend/` directory:
  ```bash
  cd backend
  ```
- Create and activate a virtual environment:
  ```bash
  python -m venv .venv
  # Windows
  .venv\Scripts\activate
  # macOS/Linux
  source .venv/bin/activate
  ```
- Install dependencies (including dev tools):
  ```bash
  pip install -e .[dev]
  ```
- Run the tests:
  ```bash
  pytest tests/ -v
  ```

#### Frontend (React + TypeScript)
*(Scaffolding planned for upcoming phases)*
- Navigate to the `frontend/` directory and install dependencies:
  ```bash
  npm install
  ```
- Start the development server:
  ```bash
  npm run dev
  ```

### 4. Create a Feature Branch
Create a branch from `main` using a descriptive name:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bugfix-name
```

---

## 🛠️ Coding Standards & Quality

To maintain a clean and reliable codebase, please adhere to:
- **Clean Architecture Principles**: Keep business logic out of API routes and repositories. Use service classes to coordinate operations.
- **Typing**: Use static type hints for Python (PEP 484) and TypeScript.
- **Linting & Formatting**:
  - Python: Use `ruff` for formatting and linting check.
  - TypeScript: Use `eslint` and `prettier`.
- **Tests**: Write unit and integration tests for any new service layer or logic modifications. Ensure all existing tests pass before submitting.

---

## 📥 Submitting a Pull Request (PR)

1. **Commit Guidelines**: Use clear, structured git commit messages (e.g. `feat(routing): add dynamic pricing evaluation`, `fix(auth): handle expired token refreshes`).
2. **Push to Your Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Submit the PR**: Open a PR from your branch against the `main` branch of `umeshpunia/ai-model-rotation`.
4. **Description**: Fill out the Pull Request Template describing the problem solved, changes made, and verification steps.
5. **Review**: Maintainers will review your PR and suggest edits if necessary.

Thank you again for contributing to AI Gateway Pro!
