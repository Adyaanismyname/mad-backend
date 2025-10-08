**PROJECT TECHNOLOGIES/CONVENTIONS PROPOSAL**

---
### 1. Technology Choices and Rationale

**Frontend: React Native + TypeScript**

* TypeScript is preferred over JavaScript for improved type safety, better tooling support, and easier debugging.
* Linting and formatting will be handled by ESLint and Prettier.

**Backend: FastAPI (async)**

* We’ll use asynchronous endpoints for scalability and responsiveness.

**Database Layer: Async SQLAlchemy + Alembic**

* SQLAlchemy (2.0 async API) provides an ORM with strong typing, async support, and flexibility.
* Alembic will manage database migrations in a structured way to ensure reproducibility and team synchronization.

**Testing Libraries**

* **Backend:** `pytest`, `pytest-asyncio`, and `httpx` for async testing.
* **Frontend:** `Jest` with React Native Testing Library (to be explored more thoroughly as the project matures as I have no experience with it, you can suggest alternatives).

---

### 2. Repository Structure

We can use a **monorepo** layout to simplify development, CI/CD, and dependency management.:

```
project-root/
│
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt or pyproject.toml
│   └── alembic/
│
├── frontend/
│   ├── src/
│   ├── __tests__/
│   ├── package.json
│   └── tsconfig.json
│
├── .github/workflows/
│   └── ci.yml
│
├── .gitignore
├── README.md
├── CONTRIBUTING.md
└── .env.example
```

---

### 3. Git Strategy — GitHub Flow

We’ll follow the **GitHub Flow**, which is simple and works well for small teams:

1. The `main` branch always contains production-ready, deployable code.
2. Each new feature or fix should be developed on a **short-lived branch** derived from `main`.
3. When ready, open a **pull request (PR)** to merge back into `main`.
4. CI must pass, and at least one team member should review the PR before merging.
5. Direct pushes to `main` are prohibited; only PR merges are allowed.

**Branch Naming Convention**

* `feature/<short-description>`
* `fix/<issue-or-bug>`
* `chore/<task-name>`
* `hotfix/<critical-patch>`

Example:

* `feature/add-login-screen`
* `fix/issue-23-db-connection`
* `chore/update-ci-config`

---

### 4. Commit Message Convention

We’ll use a **simplified Conventional Commits** style for clarity and consistency.
Format:

```
<type>(optional-scope): short description

[optional longer description]

[optional footer for issue links or breaking changes]
```

**Allowed Types**

* `feat`: new feature
* `fix`: bug fix
* `docs`: documentation only changes
* `chore`: non-functional changes (e.g., config, CI)
* `refactor`: code change that neither fixes a bug nor adds a feature
* `test`: adding or modifying tests

**Examples**

* `feat(auth): add JWT refresh tokens`
* `fix(ui): handle empty state on profile screen`
* `chore: update pre-commit hook versions`

---

### 5. Continuous Integration (CI) using GitHub Actions

We’ll use **GitHub Actions** for automated testing and linting before merging code.
Every PR should trigger the following workflows:

**Backend CI steps**

1. Install dependencies using `uv`.
2. Run tests using `pytest` (with async support via `pytest-asyncio` and `httpx`).
3. Optionally run linters (`ruff`, `flake8`, `black`, or `isort`).
4. Generate coverage reports for visibility.

**Frontend CI steps**

1. Install dependencies with `yarn install --frozen-lockfile`.
2. Run tests using `jest` (and later integrate React Native Testing Library).
3. Optionally run `eslint` and `prettier --check` for consistency.

**Workflow Example (simplified)**

```yaml
name: CI

on: [pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: cd frontend && yarn install --frozen-lockfile
      - run: cd frontend && yarn test --passWithNoTests
```

**Branch Protection Rules**

* Require PR approval before merging.
* Require all CI checks to pass.
* Disallow force pushes or direct commits to `main`.

---

### 6. Linting and Formatting (Optional but Recommended)

**Backend**
* Try to follow PEP 8 style guide (https://peps.python.org/pep-0008/).
* Use `ruff` or `flake8` for linting.
* Use `black` for code formatting.
* Use `isort` for import sorting.

**Frontend**

* Use `eslint` with TypeScript support (`@typescript-eslint` plugin).
* Use `prettier` for code formatting.

**Automation**

* Add `pre-commit` hooks (Python) and `husky` (JS) to automatically run formatters and linters before committing.

---

### 7. .gitignore and Environment Files

We’ll create a comprehensive `.gitignore` using GitHub templates for Python and React Native.
Important directories to ignore:

```
# Python
__pycache__/ (not ignored in first commit)
*.py[cod]
.env
.venv/
.mypy_cache/

# Node / React Native
node_modules/
android/.gradle/
ios/build/
*.keystore

# System / IDE
.vscode/
.idea/
.DS_Store
```

---

### 8. Database and Migrations

**ORM:** Async SQLAlchemy
**Migrations:** Alembic

* Use the async engine and session pattern recommended in SQLAlchemy 2.0.
* Write database models using declarative syntax with type hints.
* Manage migrations using Alembic commands (`alembic revision --autogenerate`, `alembic upgrade head`).
* Use separate configurations for development, testing, and production.

**Database setup**

* Use PostgreSQL locally with Docker Compose.
* Optionally we can use SQLite for local fast testing.

---

### 9. Testing Strategy

**Backend**

* Unit tests with `pytest` and async fixtures.
* Integration tests using `httpx.AsyncClient` to test endpoints through FastAPI’s ASGI interface.
* Mock external dependencies where needed.

**Frontend**

* Unit/component tests using Jest and React Native Testing Library.
* Snapshot tests for UI components.

**Test Structure**

```
backend/tests/
  ├── unit/
  ├── integration/
  └── e2e/

frontend/__tests__/
  ├── components/
  ├── screens/
  └── hooks/
```

---

### 10. Developer Experience

* Provide a one-command setup for new devs (`make dev` (makefile) or `scripts/dev.sh`) that starts backend, frontend, and DB containers.
* Use Docker Compose for consistent environments across machines.
* Enable hot-reloading in both frontend and backend.
* Using  **uv** for backend dependency management for easier reproducibility.

---

### 11. Security and Maintenance

* Store secrets securely in GitHub Secrets (never in `.env` files committed to the repo).
* Add basic request logging and error handling middleware on the backend.

---

### 12. Quality Gates Before Merge

A pull request can only be merged if:

1. CI passes successfully (tests + optionally lint).
2. Code is reviewed and approved by at least one other team member.
3. The branch has no merge conflicts with `main`.
4. All commits follow the defined message convention.

---

### 13. Recommendation on Unfamiliar Libraries/Tools

Reading **official documentation** (FastAPI, SQLAlchemy, Alembic, React Native, Jest, uv etc.) before using AI-generated code for libraries that you are not familiar with is strongly encouraged.
AI can assist with:

* Understanding unfamiliar APIs or errors.
* Generating boilerplate templates.

However, no AI output should be merged without review, understanding, and verification.


---

### 14. Logging — Structlog

**Overview**:
We’ll use **Structlog** for backend logging in the FastAPI application. Structlog provides structured, JSON-based logging, which makes logs easier to parse, search, and analyze.


**Best Practices**

* Use consistent event names and keys in logs (e.g., `user_id`, `endpoint`, `status_code`).
* Avoid logging sensitive information (passwords, tokens, personal data).
* In production, use JSON logs for better observability and centralized log management.

---

### 15. Dependency Management: uv

**Overview**
We’ll use **uv** as the Python dependency manager for the backend.

**Implementation Plan**

1. Install uv globally (`pip install uv` or download from official releases).
2. Initialize dependencies:

   ```bash
   uv init
   uv add fastapi uvicorn sqlalchemy alembic structlog pytest httpx
   ```
3. Commit `uv.lock` to the repository for reproducible environments.
4. Use uv commands in CI/CD instead of pip:

   ```bash
   uv sync
   pytest
   ```

**Best Practices**

* Always update dependencies via `uv update <package>` to keep the lockfile consistent.
* Commit both `pyproject.toml` and `uv.lock`.
* In CI, run `uv sync --frozen` to ensure exact dependency versions.
* Prefer using virtual environments managed by uv instead of system-wide installs.

---


### 16. Additional Suggestions for Future Iterations (AI generated, I am not aware of these tools)

* Introduce **Docker-based local development** (backend + DB).
* Add **E2E mobile testing** with Detox or Maestro.
* Implement **Sentry** for crash and error tracking.
* Automate versioning and changelog generation based on commit messages.
* Set up **pre-release builds** for mobile apps via GitHub Actions.
* Evaluate **monorepo tooling** like Nx or Turborepo if build times increase.

---
