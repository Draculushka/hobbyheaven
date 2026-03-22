---
description: "Create, implement, or review test plans based on code changes"
---

# Test Plan Generator

Generate, implement, or review structured test plans for changes based on git diff analysis. Usage: `/testplan $ARGUMENTS`

**Scope:** `$ARGUMENTS` (default: all uncommitted changes)

---

## Help

If `$ARGUMENTS` is `help`, print the following usage guide and STOP (do not generate a test plan):

```
/testplan — Generate, implement, or review test plans for code changes

Usage:
  /testplan                     All uncommitted changes (staged + unstaged) — default
  /testplan branch              All changes on current branch vs main
  /testplan branch:<name>       Compare branch <name> against main
  /testplan commit              Last commit only
  /testplan last                Same as commit
  /testplan commit:<hash>       Specific commit by hash
  /testplan uncommitted         Same as default — explicit
  /testplan wip                 Same as uncommitted
  /testplan staged              Staged changes only
  /testplan <N>                 Last N commits
  /testplan <path or glob>     Specific files (e.g. api/endpoints/**)
  /testplan <plan file>         Files from plan's "Files Changed" table
  /testplan implement           Implement tests from auto-discovered test plan
  /testplan implement <path>    Implement tests from explicit test plan file
  /testplan run                 Alias for implement
  /testplan review-tests        Review existing tests, output quality report, stop
  /testplan help                Show this help

Examples:
  /testplan                          → test plan for uncommitted work
  /testplan branch                   → test plan for everything on this branch vs main
  /testplan wip                      → same as default
  /testplan commit:abc1234           → test plan for one specific commit
  /testplan 5                        → last 5 commits
  /testplan docs/plans/feedback.md   → test plan based on a plan file
  /testplan implement                → implement tests from test plan for current branch
  /testplan implement docs/testing/test-plan-chat.md → implement from explicit plan
  /testplan review-tests             → review existing tests, report quality issues

Output:
  Generate mode: saves to docs/testing/test-plan-{branch-name}.md
  Review mode:   saves to docs/testing/test-review-report-YYYY-MM-DD.md
  Groups changes into features, checks existing test coverage,
  marks scenarios as TODO / COVERED / PARTIAL / DONE / DEFERRED / FAILING.
```

---

## Workflow

### Step 0: Mode Detection

Determine the execution mode based on `$ARGUMENTS` BEFORE proceeding to any other step:

| Argument | Mode | Action |
|----------|------|--------|
| `implement` or `run` | Implement | Execute **Implement Workflow** (Steps I-0 → I-7) |
| `implement <path>` | Implement | Same, with explicit plan file path |
| `review-tests` | Review | Execute only **Step I-2** (Review Existing Tests), output structured review report, then STOP |
| Anything else | Generate | Continue to Steps 1–9 below (the generate workflow) |

If mode is **Implement** → jump to [Implement Workflow](#implement-workflow).
If mode is **Review** → jump to [Step I-2: Review Existing Tests](#step-i-2-review-existing-tests), run it, output report, stop.

---

### Step 1: Identify Changes

Determine scope based on `$ARGUMENTS`:

| Argument | Scope | Git commands |
|----------|-------|--------------|
| _(empty)_ or `uncommitted` or `wip` | Unstaged + staged changes | `git diff --name-only HEAD` + `git diff HEAD` + `git diff --stat HEAD` |
| `staged` | Staged changes only | `git diff --cached --name-only` + `git diff --cached` |
| `branch` | All changes on current branch vs main | See "Branch mode" below |
| `branch:<name>` | Compare branch `<name>` vs main | `git diff main...<name> --name-only` |
| `commit` or `last` | Last commit only | `git diff HEAD~1..HEAD --name-only` + `git diff HEAD~1..HEAD` |
| `commit:<hash>` | Specific commit | `git diff <hash>~1..<hash> --name-only` |
| Number N | Last N commits | `git log --oneline -N` + `git diff HEAD~N..HEAD` |
| File path or glob | Specific files | Direct read |
| Plan file (`.md`) | Files from plan's "Files Changed" table | Read plan, extract file list |

#### Branch mode

When analyzing a full branch, gather FOUR inputs in parallel:

```bash
# 1. Changed files (what changed)
git diff main...HEAD --name-only

# 2. Commit history — short (for feature grouping)
git log main...HEAD --oneline --no-merges

# 3. Commit history — full messages (for understanding intent)
git log main...HEAD --format="%H %s" --no-merges

# 4. Diff stats (how much changed — prioritize large changes)
git diff main...HEAD --stat
```

**Feature grouping:** Group commits into logical features based on prefixes:
- `feat:` → new feature
- `fix:` → bug fix
- `refactor:` → refactoring
- `test:` → test-only changes (skip — already tested)
- `docs:` → documentation (skip — no tests needed)
- `chore:` → maintenance

#### Uncommitted mode (`uncommitted`, `wip`, `staged`)

Read the **actual diff content** (not just file names):

```bash
git diff HEAD                      # full diff for uncommitted
git diff --cached                  # full diff for staged only
```

Since there are no commit messages, infer the purpose of changes from the diff content itself.

#### Handling large diffs (>30 files)

1. **Prioritize by risk:** Security changes > business logic > API changes > UI > config > docs
2. **Group by feature:** Use commit messages or related file paths to cluster
3. **Skip test files:** Files matching `test_*.py`, `tests/` — these ARE the tests
4. **Skip non-logic files:** `requirements.txt`, `*.md`, `docker-compose.yml`, `nginx.conf`
5. **Read strategically:** For each feature group, read the 2-3 most important source files + their existing tests

### Step 2: Analyze Existing Test Coverage

Before designing new tests, check what's already covered:

```bash
# Find test files added/modified in this diff
git diff main...HEAD --name-only | grep -E 'test_.*\.py$'
```

For each changed source file, check if a test file exists:
- `api/endpoints/auth.py` → look for `tests/test_auth.py` or `tests/test_main.py`
- `services/hobby_service.py` → look for `tests/test_hobby_service.py`

Read existing test files to understand:
- What scenarios are already covered
- What naming conventions are used
- What test helpers/fixtures exist
- What mocking patterns are established

**Mark already-tested scenarios as COVERED** in the test plan.

### Step 3: Classify by Layer

Map each changed file to its layer and testing approach:

| Path prefix | Layer | Testing approach | Test location | Run command |
|-------------|-------|-----------------|---------------|-------------|
| `api/endpoints/` | API | Integration (TestClient) | `tests/test_*.py` | `PYTHONPATH=. pytest tests/ -v` |
| `services/` | Business Logic | Unit + Integration | `tests/test_*.py` | `PYTHONPATH=. pytest tests/ -v` |
| `core/` | Security/Config | Unit | `tests/test_*.py` | `PYTHONPATH=. pytest tests/ -v` |
| `models/` | Data Layer | Unit + Migration | `tests/test_*.py` | `PYTHONPATH=. pytest tests/ -v` |
| `templates/` | UI | Manual / Playwright | Manual check or E2E | Manual |
| `migrations/` | DB Schema | Migration dry-run | `alembic upgrade head` | `alembic upgrade head --sql` |

### Step 4: Testability Analysis

For each changed module/function, perform a **7-point analysis** before designing test cases:

1. **Unit under test** — What is the exact function, method, or class being tested?
2. **Inputs** — All parameters, form fields, query params, environment variables
3. **Outputs** — Return values, response body, side effects (DB writes, Redis ops, file uploads)
4. **Dependencies** — External services (Redis, PostgreSQL), file system that need mocking
5. **Existing tests** — What test file already covers this? What scenarios are missing?
6. **Cross-layer impact** — Does this change affect templates, services, or security?
7. **Cross-cutting triggers** — Scan against [trigger checklist](#step-7-cross-cutting-test-triggers) — which triggers fire?

Document this analysis briefly per feature group (not per individual function).

### Step 5: Apply Test Design Techniques

For each test case, apply the relevant techniques:

| Code | Technique | When to apply | Example |
|------|-----------|--------------|---------|
| **EP** | Equivalence Partitioning | Input accepts a range/set of values — test one value per class | Tag input: empty, single tag, multiple tags, special chars |
| **BVA** | Boundary Value Analysis | Numeric limits, string lengths, array sizes | Password: 5 chars (too short), 6 (min valid), 64 (max valid), 65 (too long) |
| **DT** | Decision Table | Multiple conditions combine to produce different outcomes | is_admin + is_owner → who can delete hobby |
| **ST** | State Transition | Entity moves through states with defined transitions | User: created → verified → active → soft-deleted |
| **DA** | Domain Analysis | Validate business rules, config constants, enum values | Persona limit = 3, verification code TTL = 10 min |
| **EG** | Error Guessing | Likely failure points based on experience | null inputs, empty strings, SQL injection in search |
| **PT** | Pairwise Testing | Too many input combinations to test exhaustively | Search + pagination + persona filter |

Label each test case with technique(s): `[EP]`, `[BVA]`, `[DT]`, `[ST]`, `[DA]`, `[EG]`, `[PT]`.

### Step 6: Generate Test Plan

For each feature/change, produce test cases with this structure:

```
### [File/Module name]

**What changed:** Brief description of the change

**Header metadata:**
- Base commit: `abc1234`
- Commits in scope: N
- Layers: API, Services, Core
- Changed files: N

**Preconditions:** List any required state, services, or data

**Test ID** | **Type** | **Technique** | **Description** | **Priority** | **Status**
TP-01 | Unit | EP, BVA | Description | P0 | TODO
TP-02 | Integration | DT | Description | P1 | COVERED

**Test code location:** `tests/test_auth.py`

#### TP-01: [Test case name]
- **Technique:** EP + BVA
- **Arrange:** Setup description
- **Act:** What action to perform
- **Assert:** Expected result
- **Equivalence classes:** valid class, invalid class 1, invalid class 2
- **Boundary values:** min-1, min, min+1, max-1, max, max+1
- **Implementation hint:** Brief guidance on how to implement (mocking strategy, setup pattern)

##### Sub-scenarios
| # | Input | Expected | Technique |
|---|-------|----------|-----------|
| a | Valid title "Шахматы" | Created | EP |
| b | Empty title "" | Rejected 422 | BVA |
| c | Title 256 chars | Rejected 422 | BVA |
```

Status values:
- **TODO** — needs implementation
- **COVERED** — already tested
- **PARTIAL** — some scenarios tested, needs expansion
- **DONE** — implemented during this session (implement mode)
- **DEFERRED** — skipped with documented reason
- **FAILING** — test exists but currently fails

### Step 7: Cross-Cutting Test Triggers

Scan the diff for each trigger condition. If true, add corresponding test cases.

#### 1. Access Control
If endpoints or auth guards changed:
- [ ] **IDOR/BOLA** — user A cannot edit/delete user B's hobbies or personas
- [ ] **Ownership chain** — hobby → persona → user ownership validated
- [ ] **Missing auth** — unauthenticated requests return 401 or redirect to login
- [ ] **Admin vs user** — non-admin cannot delete others' hobbies
- [ ] **Soft-deleted users** — deleted users cannot authenticate or access resources

#### 2. Input Validation
If form handlers, Pydantic schemas, or services changed:
- [ ] **Boundary values** — min/max lengths, 0, -1, empty string, None
- [ ] **Injection** — SQL injection in search (`'; DROP TABLE --`), XSS in description (`<script>alert(1)</script>`)
- [ ] **LIKE-injection** — `%` and `_` chars in search input
- [ ] **Special characters** — unicode, null bytes in titles/tags
- [ ] **Format validation** — invalid email format
- [ ] **Oversize input** — files exceeding 5MB, descriptions exceeding reasonable limits
- [ ] **File upload** — wrong MIME type, no extension, executable files

#### 3. Error Handling
If error handling or error responses changed:
- [ ] **No internal leaks** — errors don't contain stack traces, SQL queries, or file paths
- [ ] **Consistent error format** — proper HTTP status codes (401, 403, 404, 422)
- [ ] **Graceful degradation** — behavior when Redis is unavailable

#### 4. Auth & Session
If authentication, JWT, login, or session code changed:
- [ ] **JWT edge cases** — expired token, invalid signature, malformed token
- [ ] **Cookie flags** — HttpOnly, Secure, SameSite
- [ ] **Rate limiting** — brute-force verification codes blocked after 5 attempts
- [ ] **Verification flow** — code TTL (10 min), cooldown (60 sec), attempt limits
- [ ] **Logout** — cookie properly cleared

#### 5. State Transitions
If user/hobby/persona states changed:
- [ ] **User lifecycle:** created → verified → active → soft-deleted
- [ ] **Soft delete flow:** request code → enter code → account frozen → 30 days → permanent delete
- [ ] **Persona limits:** max 3 per user, at least 1 default
- [ ] **Idempotency** — same action twice produces same result

#### 6. SQL / Database
If models, migrations, or queries changed:
- [ ] **Migration correctness** — upgrade and downgrade work
- [ ] **NULL inputs** — queries with NULL parameters don't error
- [ ] **Pagination boundaries** — page=0, page=-1, page beyond total
- [ ] **Constraint violations** — unique username, unique email (proper error, not 500)
- [ ] **Soft-delete filtering** — deleted users excluded from all relevant queries
- [ ] **N+1 queries** — joinedload/selectinload used where needed

#### 7. HTML Sanitization
If description handling or template rendering changed:
- [ ] **XSS prevention** — `<script>`, `<img onerror>`, `javascript:` in descriptions
- [ ] **Allowed tags** — only `b, i, em, strong, a, ul, ol, li, p, br, h2, h3, blockquote`
- [ ] **Protocol filtering** — only `http`, `https`, `mailto` in links
- [ ] **Template escaping** — `{{ var }}` auto-escaped, `| sanitize` applied correctly

#### 8. File Uploads
If image upload handling changed:
- [ ] **Extension validation** — only `.jpg, .jpeg, .png, .gif, .webp` allowed
- [ ] **Size limit** — files > 5MB rejected
- [ ] **UUID filenames** — no path traversal possible
- [ ] **Cleanup** — old images deleted on update

### Step 8: Prioritize

Mark each test case with priority:
- **P0 (Critical)** — Could break production, data corruption, security
- **P1 (High)** — Core business logic, API contracts, data integrity
- **P2 (Medium)** — Non-critical features, UI, logging
- **P3 (Low)** — Cosmetic, docs, config

**Minimum coverage rule:** Every P0 and P1 item from cross-cutting triggers MUST have a corresponding test case.

### Step 9: Summary & Save

Save the test plan to `docs/testing/test-plan-{branch-name}.md` (use `git branch --show-current` to get branch name; sanitize `/` → `-`). If on `main`, fall back to `test-plan-{description}.md`.

Output a summary:

```
## Test Plan Summary — YYYY-MM-DD

### Header
- **Base commit:** `abc1234`
- **Commits in scope:** N
- **Layers:** API, Services, Core, Models, Templates
- **Changed files:** N

### Features on This Branch

| # | Feature | Commits | Layers | Key files |
|---|---------|---------|--------|-----------|
| F1 | [name] | abc, def | API, Services | `auth.py`, `auth_service.py` |

### Existing Test Coverage

| Test file | Tests | Covers |
|-----------|-------|--------|
| `tests/test_main.py` | 17 | F1: registration, login, home page |

### Test Plan Summary

| Priority | New Tests | Update Existing | Already Covered | Total |
|----------|-----------|-----------------|-----------------|-------|
| P0       | 2         | 1               | 0               | 3     |
| P1       | 5         | 2               | 3               | 10    |
| P2       | 1         | 0               | 4               | 5     |
| **Total**| **8**     | **3**           | **7**           | **18**|

### Cross-Cutting Tests

| # | Trigger | Test case | Priority | Status |
|---|---------|-----------|----------|--------|
| S-1 | Access Control | User A cannot delete User B's hobby | P0 | TODO |
| S-2 | Input Validation | SQL injection in search parameter | P0 | COVERED |

### Files to create/modify:
- `tests/test_auth.py` (NEW)
- `tests/test_hobbies.py` (NEW)
- `tests/test_main.py` (UPDATE)

### Verification Checklist:
- [ ] `SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. pytest tests/ -v`
```

---

## Implement Workflow

This workflow executes when mode is **Implement** (`/testplan implement` or `/testplan run`).

### Step I-0: Pre-flight Environment Check

Check that required tools are available before starting:

| Dependency | Check command | Required for |
|------------|---------------|--------------|
| Python 3.12+ | `python3 --version` | All tests |
| pytest | `python3 -m pytest --version` | All tests |
| pip packages | `pip list \| grep -E 'fastapi\|sqlalchemy\|pytest'` | Unit + integration |

**Logic:**
- Missing dependency required for **unit tests** → **STOP** with error message listing what's missing
- Missing dependency for **E2E/integration only** → proceed with unit tests, note skipped E2E tests in report

### Step I-1: Discover and Parse Test Plan

1. **Auto-detect test plan file:**
   - Get current branch: `git branch --show-current`
   - Look for: `docs/testing/test-plan-{branch-name}.md` (with `/` → `-` sanitization)
   - If not found, list `docs/testing/test-plan-*.md` and pick the most recently modified
2. **Explicit path override:** If `$ARGUMENTS` includes a path after `implement`, use that file
3. **Parse the test plan:**
   - Extract summary table (Test ID, Type, Technique, Description, Priority, Status)
   - Extract individual test case sections (Arrange/Act/Assert, sub-scenarios)
   - Build a work list of all items with status `TODO` or `PARTIAL`
4. **Pre-existing failure snapshot:**
   - Run existing test suites: `SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. pytest tests/ -v`
   - Capture any current failures to `/tmp/pre-existing-failures.txt`
   - These failures are NOT caused by new tests — don't try to fix them

### Step I-2: Review Existing Tests

**Always runs** in both Implement mode and Review-tests mode.

For each test file related to the changed components, check for quality issues:

| Check | What to look for | Severity |
|-------|------------------|----------|
| Skipped tests | `@pytest.mark.skip`, `pytest.skip()` | HIGH |
| Weakened assertions | Bare `assert` without value check, `assert True` | MEDIUM |
| Missing AAA | Tests without clear Arrange/Act/Assert separation | LOW |
| Missing sub-scenarios | Test covers happy path but not edge cases from plan | HIGH |
| Dead tests | Tests that never fail (always pass regardless of code) | HIGH |
| Duplicated setup | Same setup repeated across tests instead of using fixtures | LOW |
| Missing error paths | No tests for 401, 403, 404, 422 responses | HIGH |

**If `review-tests` mode:** Output a structured review report with findings per file, **save it to `docs/testing/test-review-report-YYYY-MM-DD.md`**, and stop.

**Report format:**
```
## Test Review Report — YYYY-MM-DD

### Summary
- Files reviewed: N
- Issues found: N (HIGH: X, MEDIUM: Y, LOW: Z)

### Aggregate by Layer
| Layer | Files | Tests | HIGH | MEDIUM | LOW | Total |
|-------|------:|------:|-----:|-------:|----:|------:|

### HIGH Severity Findings
| # | File | Line(s) | Issue | Recommendation |
|---|------|---------|-------|----------------|

### MEDIUM Severity Findings
| # | File | Line(s) | Issue | Recommendation |
|---|------|---------|-------|----------------|

### LOW Severity Findings
| Category | Count | Files affected |
|----------|------:|----------------|

### Top Recommendations
1. ...
```

**Save to:** `docs/testing/test-review-report-YYYY-MM-DD.md`

### Step I-3: Implement TODO Tests

Process test plan items in priority order: **P0 → P1 → P2 → P3**.

For each TODO or PARTIAL item:

1. **Read the target source file** to understand the code under test
2. **Read existing test file** (if any) to match style, imports, and patterns
3. **Determine placement:**

| Layer | Test location | Naming |
|-------|--------------|--------|
| API endpoints | `tests/test_{endpoint_name}.py` | `test_{feature}.py` |
| Services | `tests/test_{service_name}.py` | `test_{service}.py` |
| Core/Security | `tests/test_security.py` | `test_{module}.py` |
| Models | `tests/test_models.py` | `test_models.py` |

4. **Match existing test patterns:**

| Pattern | Reference |
|---------|-----------|
| TestClient with DB override | `tests/conftest.py` — `client` fixture |
| In-memory SQLite with StaticPool | `tests/conftest.py` — engine setup |
| Auth helper (create user + JWT cookie) | Create user via DB, token via `create_access_token()` |
| Redis mock | `@patch("services.auth_service.redis_client")` |
| File upload mock | `UploadFile` with `io.BytesIO` |

5. **Write the test code** following AAA pattern, matching existing style
6. **PARTIAL handling:** Prefer adding new `test_` functions. Name with scenario ID from the plan (e.g., `test_tp05_rejects_expired_token`)
7. **DEFERRED items:** Skip with logged reason in the completion report. Do NOT create skipped tests.

### Step I-4: Run Tests

After implementing tests, run them:

```bash
SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. python3 -m pytest tests/ -v
```

Run only the specific test file first for faster feedback:
```bash
SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. python3 -m pytest tests/test_auth.py -v -x
```

### Step I-5: Debug Loop

When tests fail, follow this protocol:

1. **Parse the failure** — read the error message, stack trace, assertion diff
2. **Read the application code** — understand what the code actually does vs. what the test expects
3. **Diagnose:**
   - **Assertion failure** → likely a bug in application code (Rule 2: Code is Guilty). Fix the application code.
   - **Import error in test** → fix the test code (import path, missing dependency)
   - **Setup/teardown error** → fix test infrastructure (missing mock, wrong fixture)
4. **Fix** — apply the minimal fix
5. **Selective re-run** — run only the failing test, not the entire suite
6. **Regression check** — compare against pre-existing failure snapshot from Step I-1

**Max 5 iterations per test.** If a test still fails after 5 attempts:
- Mark as `FAILING` in the test plan
- Document the issue in the completion report
- Move to the next test

**Rollback protocol:**
- If a fix causes NEW failures not in the pre-existing snapshot → **revert the fix**
- If a fix touches application code and causes regressions → **revert**, document as technical debt
- Never let the debug loop leave the codebase in a worse state than before

### Step I-6: Update Test Plan

After all tests are implemented and run, update the test plan file:

- `TODO → DONE` — test implemented and passing
- `PARTIAL → DONE` — missing scenarios added and passing
- `TODO → FAILING` — test implemented but failing (with note)
- `DEFERRED` — unchanged (already skipped with reason)

### Step I-7: Completion Report

Output a structured completion report:

```
## Implementation Report — YYYY-MM-DD

### Summary

| Status | Count |
|--------|-------|
| DONE | X |
| FAILING | Y |
| DEFERRED | Z |
| Skipped (env) | W |
| **Total** | **N** |

### New Tests Written

| # | Test ID | File | Test name | Status |
|---|---------|------|-----------|--------|
| 1 | TP-01 | `tests/test_auth.py` | test_rejects_expired_token | DONE |
| 2 | TP-03 | `tests/test_hobbies.py` | test_like_injection_escaped | DONE |

### Run Commands

To re-run all new tests:
- `SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. pytest tests/ -v`

### Application Bugs Found

| # | Location | Description | Severity | Fix applied? |
|---|----------|-------------|----------|--------------|
| 1 | `hobby_service.py:42` | Off-by-one in pagination | P1 | Yes |

### Technical Debt / Impediments

- [ ] Redis mock incomplete — cannot test cache expiry scenarios
- [ ] No test fixtures for multi-persona scenarios
```

---

## Critical Rules for Implementation

These rules apply whenever implementing tests (Implement Workflow):

### Rule 1: No Skipping
Never add `@pytest.mark.skip` or `pytest.skip()` to unit tests. The only acceptable skip is on integration tests with a documented reason (e.g., "requires Redis not available in CI").

### Rule 2: Code is Guilty
When a test fails, assume the **application code** has a bug — not the test. Investigation order:
1. Read the application code
2. Check the spec/requirements
3. Only then consider the test code might be wrong

### Rule 3: No Weakening
Never weaken tests to make them pass:
- Never remove assertions
- Never widen expected boundaries (e.g., changing `assert x == 5` to `assert x > 0`)
- Never loosen mocks
- **Acceptable:** fix typos, update setup for API changes, add MORE assertions

### Rule 4: Debug Protocol
Strict sequence: Parse failure → Read app code → Diagnose → Fix → Selective re-run → Regression check. If regression detected → rollback immediately. Max 5 iterations.

### Rule 5: Respect the Plan
Every scenario in the test plan MUST have a corresponding assertion. Implement all sub-scenarios, not just the happy path. If a test case has sub-scenario table, each row = one assertion.

### Rule 6: No Test-Only Visibility Changes
Never export internal helpers, private methods, or module internals solely for testing. Test via the public API. Use `conftest.py` fixtures for setup, not by reaching into private state.

---

## Project-Specific Test Patterns

### Python — FastAPI + SQLAlchemy (HobbyHold)

```python
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db
from models import Base, User, Persona, Hobby
from core.security import create_access_token, get_password_hash


# --- Fixtures (in conftest.py) ---

@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override():
        yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Auth helper ---

def create_test_user(db, email="test@example.com", password="password123", username="testuser", verified=True):
    user = User(email=email, hashed_password=get_password_hash(password), is_active=verified)
    db.add(user)
    db.flush()
    persona = Persona(user_id=user.id, username=username, is_default=True)
    db.add(persona)
    db.commit()
    return user, persona


def auth_cookie(email="test@example.com"):
    token = create_access_token(data={"sub": email})
    return {"access_token": f"Bearer {token}"}


# --- Test example ---

def test_create_hobby_requires_auth(client):
    """[EP] Unauthenticated user cannot create hobby"""
    response = client.post("/create-hobby", data={"title": "Test", "description": "Desc"})
    assert response.status_code in (303, 401)


def test_user_cannot_edit_others_hobby(client, db):
    """[DT] IDOR: user A cannot edit user B's hobby"""
    user_a, persona_a = create_test_user(db, "a@test.com", username="user_a")
    user_b, persona_b = create_test_user(db, "b@test.com", username="user_b")
    hobby = Hobby(title="Test", description="Desc", persona_id=persona_b.id)
    db.add(hobby)
    db.commit()

    # User A tries to edit User B's hobby
    client.cookies = auth_cookie("a@test.com")
    response = client.get(f"/edit/{hobby.id}")
    assert response.status_code == 403


@patch("services.auth_service.redis_client")
def test_verification_code_timing_safe(mock_redis, client, db):
    """[EG] Verification code comparison is timing-safe"""
    mock_redis.get.return_value = "123456"
    # Test passes if hmac.compare_digest is used instead of ==
```

### Key patterns:
- **TestClient** with dependency override for SQLite in-memory DB
- **StaticPool** ensures all threads share same in-memory DB
- **Auth helper** creates user + persona + JWT cookie
- **Redis mock** via `@patch` decorator
- **File upload mock** via `io.BytesIO` wrapped in `UploadFile`
- Test file naming: `test_*.py`
- Fixture scope: `function` (clean DB per test)

---

## Rules

- Communicate in Russian
- **ALWAYS read and understand the changed files before proposing test cases** — never speculate about code you haven't inspected
- Focus on testing CHANGED behavior, not writing tests for unchanged code
- Check existing tests BEFORE proposing new ones — avoid duplicates
- Use AAA pattern (Arrange-Act-Assert) for test case descriptions
- Every test case MUST reference at least one test design technique (EP, BVA, DT, ST, DA, EG, PT)
- Every P0 and P1 item from cross-cutting triggers MUST have a corresponding test case
- Test file naming: `test_*.py`, fixtures in `conftest.py`
- In **Generate mode**: do NOT write test code — only the plan. User will ask to implement if needed
- In **Implement mode**: write the actual test code, run it, fix issues
- Run command: `SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. pytest tests/ -v`
