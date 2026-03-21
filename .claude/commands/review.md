---
description: "Review code changes, implementation plans, or UI/UX quality"
---

# Code, Plan & UI Review

Perform a thorough review of code changes, implementation plans, or UI/UX quality.
Checks security, architecture, correctness, accessibility, and UX standards.

**Scope:** `$ARGUMENTS` (default: code review of all changes on current branch vs main)

---

## Help

If `$ARGUMENTS` is `help`, print the following usage guide and STOP (do not perform a review):

```
/review — Code, plan & UI review with security, architecture, UX, and correctness analysis

Three modes: CODE REVIEW (default), PLAN REVIEW ("plan"), UI REVIEW ("ui").

═══════════════════════════════════════════════════════════════
  CODE REVIEW — review actual code changes (default)
═══════════════════════════════════════════════════════════════

Scope:
  /review                       All changes on current branch vs main (default)
  /review branch                Same as above — explicit
  /review commit                Last commit only
  /review last                  Same as commit
  /review commit:<hash>         Specific commit by hash
  /review uncommitted           All uncommitted changes (unstaged + staged)
  /review wip                   Same as uncommitted
  /review staged                Staged changes only
  /review <path or glob>        Specific files (e.g. api/endpoints/**)

═══════════════════════════════════════════════════════════════
  PLAN REVIEW — audit implementation plan before coding
═══════════════════════════════════════════════════════════════

Scope:
  /review plan                  Auto-detect latest plan in docs/plans/
  /review plan latest           Same as above — explicit
  /review plan all              Review all unimplemented plans (summary table)
  /review plan <path>           Review specific plan file

═══════════════════════════════════════════════════════════════
  UI REVIEW — audit UI/UX of pages or components
═══════════════════════════════════════════════════════════════

Scope (same git scopes as code review, filtered to templates/ files):
  /review ui                    Changed template files on branch vs main
  /review ui wip                Uncommitted template changes
  /review ui staged             Staged template changes only
  /review ui commit             Template files in last commit
  /review ui commit:<hash>      Template files in specific commit
  /review ui <page>             Specific template (e.g. "cabinet", "profile")

═══════════════════════════════════════════════════════════════
  CATEGORIES — filter what to check
═══════════════════════════════════════════════════════════════

Combine scope + categories freely. Default (no flags): ALL categories.

  Shared (code + plan):
    +security                   OWASP Top 10, input validation, auth, secrets
    +architecture  (+arch)      SOLID, KISS, DRY, patterns, layer violations
    +lang                       Language-specific (Python, FastAPI, SQLAlchemy)
    +sql                        SQL / PostgreSQL (DDL, queries, indexes, migrations)
    +observability (+obs)       Logging, structured context
    +deploy                     Deploy impact, env vars, migration order
    +deps                       Dependency vulnerabilities (pip audit)
    +docs                       Documentation alignment (CLAUDE.md, specs)

  Code review only:
    +correctness                Logic, edge cases, error handling, race conditions
    +tests                      Test coverage, quality, determinism

  Plan review only:
    +completeness               Plan structure (context, files table, verification)
    +project                    Project-specific rules (personas, soft delete, search)

  UI review only:
    +responsive / +mobile       Responsive design, mobile-first, touch targets
    +a11y / +accessibility      WCAG 2.2 AA compliance
    +perf / +performance        Core Web Vitals (LCP, CLS, INP)
    +ux                         Nielsen's Heuristics + UX Laws
    +ds / +design-system        Tailwind tokens, consistent styling

═══════════════════════════════════════════════════════════════
  EXAMPLES
═══════════════════════════════════════════════════════════════

  Code review:
    /review                            → full review of branch (all categories)
    /review +security                  → security-only review of branch
    /review +security +sql             → security + database review
    /review wip +correctness +lang     → correctness + language on uncommitted
    /review commit +sql                → SQL review of last commit
    /review +deps                      → dependency vulnerability scan only

  Plan review:
    /review plan                       → review latest plan (all categories)
    /review plan docs/plans/foo.md     → review specific plan
    /review plan all                   → review all plans, summary table
    /review plan +arch +security       → architecture + security check on plan

  UI review:
    /review ui                         → audit changed template files on branch
    /review ui wip                     → audit uncommitted template changes
    /review ui cabinet                 → audit cabinet page
    /review ui +a11y                   → accessibility-only audit
    /review ui wip +responsive +perf   → responsive + performance on uncommitted

═══════════════════════════════════════════════════════════════
  OUTPUT
═══════════════════════════════════════════════════════════════

  Code: prints inline; branch also saves to docs/reviews/review-{branch}.md
  Plan: prints inline; modifies plan file in-place if issues found
  UI:   prints inline; saves to docs/reviews/ui-review-{target}.md

  Severity levels:
    CRITICAL  — security vulnerability or data loss risk, must fix
    HIGH      — bug or significant issue, should fix before merge
    MEDIUM    — code quality, non-critical edge case
    LOW       — style, naming, minor improvement
    INFO      — observation, no action needed

  Verdict:
    APPROVE            — no blockers, ready to merge
    APPROVE WITH NOTES — minor issues, proceed after addressing HIGH
    REQUEST CHANGES    — must fix CRITICAL/HIGH first
```

---

## Workflow

### Step 0: Parse Arguments

Split `$ARGUMENTS` into **mode**, **scope**, and **categories**:

1. **Mode**: `ui` keyword → UI mode, `plan` keyword → PLAN mode, otherwise → CODE mode
2. **Scope**: remaining arguments without `+` prefix (and without mode keyword)
3. **Categories**: arguments with `+` prefix

If no `+` flags → run ALL categories applicable to the mode.
If `+` flags provided → run ONLY those categories.

#### Code + Plan category mapping

| Flag | Section | Mode |
|------|---------|------|
| `+correctness` | 1. Correctness | Code only |
| `+completeness` | 2. Plan Completeness | Plan only |
| `+security` | 3. Security (OWASP Top 10) | Both |
| `+architecture` / `+arch` | 4. Architecture (SOLID / KISS / DRY) | Both |
| `+lang` | 5. Language-Specific | Both |
| `+sql` | 6. SQL / PostgreSQL | Both |
| `+observability` / `+obs` | 7. Observability | Both |
| `+tests` | 8. Tests | Code only |
| `+project` | 9. Project-Specific Rules | Plan primarily |
| `+deploy` | 10. Deploy Impact | Both |
| `+deps` | 11. Dependency Vulnerabilities | Both |
| `+docs` | 12. Documentation Alignment | Both |

#### UI category mapping

| Flag | Section |
|------|---------|
| `+responsive` / `+mobile` | U1. Mobile-First |
| `+a11y` / `+accessibility` | U2. Accessibility (WCAG 2.2 AA) |
| `+perf` / `+performance` | U3. Core Web Vitals |
| `+ux` | U4. Nielsen's Heuristics + UX Laws |
| `+ds` / `+design-system` | U5. Design System Compliance |

### Step 1: Identify What to Review

#### CODE mode

| Argument | Scope | Commands |
|----------|-------|----------|
| _(empty)_ or `branch` | All changes on current branch vs main | See "Branch mode" below |
| `commit` or `last` | Last commit only | `git diff HEAD~1..HEAD` |
| `commit:<hash>` | Specific commit | `git diff <hash>~1..<hash>` |
| `uncommitted` or `wip` | Unstaged + staged changes | `git diff HEAD` |
| `staged` | Staged changes only | `git diff --cached` |
| File path or glob | Specific files | Direct read |

##### Branch mode (default)

Gather context in parallel:

```bash
# 1. Changed files
git diff main...HEAD --name-only

# 2. Commit history for context
git log main...HEAD --oneline --no-merges

# 3. Full diff (the actual review target)
git diff main...HEAD

# 4. Diff stats (prioritize large changes)
git diff main...HEAD --stat
```

##### Uncommitted mode (`uncommitted`, `wip`, `staged`)

```bash
git diff --name-only HEAD          # unstaged + staged
git diff --cached --name-only      # staged only
git diff HEAD                      # full uncommitted diff
git diff --cached                  # full staged diff
```

Read the full diff content. Since there are no commit messages, infer purpose from the code.

##### Handling large diffs (>50 files or >2000 lines)

1. **Read stats first** — `git diff --stat` to identify largest changes
2. **Prioritize:** Security-sensitive > business logic > API changes > UI > config > docs
3. **Skip:** Generated files, lock files
4. **Group by layer** — review one layer at a time (api → services → core → models)
5. **Read source files** for context when the diff alone is insufficient

#### PLAN mode

| Argument | Action |
|----------|--------|
| `plan` or `plan latest` | Find most recently modified `.md` in `docs/plans/`: `ls -t docs/plans/*.md \| head -5` |
| `plan all` | List all plans, review each, produce summary table |
| `plan <path>` | Review that specific file |

For `all` mode, output a summary:
```markdown
| # | Plan | Risk | Findings | Verdict |
|---|------|------|----------|---------|
| 1 | add-comments.md | Medium | 2 HIGH, 3 MEDIUM | APPROVED WITH NOTES |
| 2 | image-gallery.md | Low | 1 MEDIUM | APPROVED |
```

**Plan mode workflow:**
1. Read the plan file in full
2. Read project foundation (`CLAUDE.md`)
3. Read component-specific context (see Step 2)
4. For each new file/module in the plan, find analogous existing code and verify patterns match
5. Run the audit checklist
6. **Modify the plan in-place** if issues found, explain each change

#### UI mode

UI mode supports the same git scopes as CODE mode — filtered to template and static files.

| Argument | Action |
|----------|--------|
| `ui` (no further args) | Changed template/static files on branch vs main: `git diff main...HEAD --name-only` filtered to `templates/` and `static/` |
| `ui wip` / `ui uncommitted` | Uncommitted template/static changes |
| `ui staged` | Staged template/static changes only |
| `ui commit` / `ui last` | Template/static files in last commit |
| `ui commit:<hash>` | Template/static files in specific commit |
| `ui <page>` | Specific template (e.g. "cabinet", "profile", "index") |

Git scope filter: after getting the file list, keep only files matching `templates/*.html`, `static/**/*.{css,js}`. Skip test files.

**UI mode workflow:**
1. Read every target file completely — NEVER speculate about code you haven't read
2. Also read related templates (base layout if exists), Tailwind config, static CSS/JS
3. Run the UI audit checklist (categories U1-U5 below)
4. Output findings with fix proposals

### Step 2: Read Project Context

ALWAYS read before reviewing:
- `CLAUDE.md` — project rules, patterns, build commands

Based on components touched:

| Component | Read |
|-----------|------|
| `api/endpoints/` | Relevant endpoint file, corresponding service in `services/` |
| `services/` | Service file, models it uses from `models/__init__.py` |
| `core/` | `config.py` (settings, synonyms), `security.py` (JWT, auth middleware) |
| `models/` | `models/__init__.py` — all SQLAlchemy models, relationships |
| `schemas/` | `schemas/__init__.py` — Pydantic validation schemas |
| `templates/` | Target template + related templates (e.g. base layout) |
| `migrations/` | Latest migration file, `alembic.ini`, `migrations/env.py` |
| `tests/` | `tests/conftest.py` (fixtures), related test files |
| Docker/deploy | `docker-compose.yml`, `Dockerfile`, `nginx/nginx.conf` |

### Step 3: Review Checklist

If `+` category flags were provided, run ONLY those categories.
Otherwise, apply ALL categories applicable to the current mode.
Always skip categories that don't apply (e.g. skip SQL if no queries, skip Deploy if no infra changes).

---

## Review Categories (Code + Plan)

### 1. Correctness _(code mode only)_

- [ ] Logic matches intended behavior (read spec/plan if unclear)
- [ ] Edge cases handled (null, empty, boundary values, concurrent access)
- [ ] Error paths return appropriate HTTP status codes
- [ ] No off-by-one errors in loops, pagination, or slicing
- [ ] Async code: no race conditions, proper exception handling
- [ ] State mutations are atomic where needed (DB transactions)

### 2. Plan Completeness _(plan mode only)_

- [ ] **Context section** — why this change is needed, what problem it solves
- [ ] **Architecture** — clear description of component interaction and data flow
- [ ] **Files Changed table** — lists all new/modified files with actions
- [ ] **Verification section** — how to test (build, run, manual check)
- [ ] **Test plan** — what tests to write
- [ ] **Migration plan** — if DB changes: Alembic migration file described
- [ ] **Deploy plan** — which Docker services need rebuild
- [ ] **No ambiguity** — plan is detailed enough for another developer to implement

### 3. Security — OWASP Top 10 Alignment

#### Input Validation
- [ ] All user input validated at boundaries (Pydantic schemas)
- [ ] String fields have length limits in Pydantic schemas
- [ ] Numeric fields clamped to reasonable bounds
- [ ] No mass assignment — explicit schema fields only
- [ ] HTML sanitized via bleach before storage (descriptions)

#### Access Control
- [ ] Auth checks (`get_current_user`) on all non-public endpoints
- [ ] No IDOR/BOLA — user can only access/modify own resources (check persona ownership)
- [ ] Admin checks (`is_admin`) for admin-only operations
- [ ] Soft-deleted users cannot authenticate

#### Error Handling
- [ ] No stack traces or internal details exposed to client
- [ ] Appropriate HTTP status codes (401, 403, 404, 422)

#### Data Protection
- [ ] No hardcoded secrets, API keys, passwords
- [ ] No PII in logs
- [ ] Secrets via environment variables and `.env`
- [ ] `.env` in `.gitignore`

#### API Security
- [ ] Rate limiting on auth endpoints (Redis-based cooldowns)
- [ ] Schema validation on request bodies
- [ ] No excessive data exposure — responses return only needed fields
- [ ] Pagination with `LIMIT` on all list queries

#### Injection Prevention
- [ ] Parameterized queries only — no string interpolation in SQL/SQLAlchemy
- [ ] No raw HTML rendering without bleach sanitization
- [ ] JWT tokens stored in HttpOnly cookies (not localStorage)

### 4. Architecture — SOLID, KISS, DRY

#### Layered Architecture Compliance
- [ ] **Endpoints** (`api/endpoints/`) — only HTTP handling, delegate to services
- [ ] **Services** (`services/`) — business logic, DB access via SQLAlchemy
- [ ] **Core** (`core/`) — configuration and security utilities only
- [ ] No layer violations (endpoints don't access DB directly, services don't handle HTTP)

#### SOLID
- [ ] **SRP** — each module/function has one responsibility
- [ ] **OCP** — extends behavior via new types, not modifying existing core logic
- [ ] **DIP** — depends on abstractions where practical

#### KISS
- [ ] Simplest solution that works — no over-engineering
- [ ] No premature abstractions (need 3+ uses before extracting)
- [ ] No "future-proofing" for hypothetical requirements

#### DRY
- [ ] Single source of truth — Pydantic schemas for validation, SQLAlchemy models for DB
- [ ] No copy-paste of existing logic — reuse existing services/utils
- [ ] BUT: duplication is better than wrong abstraction

#### Alignment with Existing Code
- [ ] Follows patterns already established in the codebase
- [ ] Uses existing shared utilities instead of creating new ones
- [ ] File structure matches project conventions

### 5. Language-Specific (Python / FastAPI / SQLAlchemy)

#### Python
- [ ] PEP 8 compliance (naming, imports, spacing)
- [ ] No unused imports
- [ ] Type hints on function signatures where practical
- [ ] No bare `except:` — catch specific exceptions
- [ ] No mutable default arguments (lists, dicts)

#### FastAPI
- [ ] Proper use of dependency injection (`Depends()`)
- [ ] Response models defined where appropriate
- [ ] Path parameters validated (type annotations)
- [ ] `HTTPException` with correct status codes
- [ ] Templates rendered via `Jinja2Templates` with proper context
- [ ] `Form()` for form data, `File()` for uploads
- [ ] Static files mounted correctly

#### SQLAlchemy
- [ ] Session properly managed (no leaked sessions)
- [ ] Relationships defined with correct `back_populates`
- [ ] Eager loading (`joinedload`) where N+1 queries likely
- [ ] `db.commit()` after mutations, `db.rollback()` on error
- [ ] No raw SQL unless absolutely necessary — use ORM methods

#### Alembic
- [ ] Migration auto-generated after model changes
- [ ] Migration reviewed before applying (check `upgrade()` and `downgrade()`)
- [ ] Never modify already-applied migrations
- [ ] Downgrade function properly reverts changes

### 6. SQL / PostgreSQL

- [ ] Migrations: atomic, sequential numbering
- [ ] Uses `sa.Column` with proper types and constraints
- [ ] Indexes on frequently queried columns (foreign keys, unique fields)
- [ ] Constraints: CHECK, UNIQUE, FK for data integrity
- [ ] No `SELECT *` equivalent — query only needed columns where performance matters
- [ ] NULL handling: proper defaults, nullable flags
- [ ] No unbounded queries: pagination with `LIMIT`/`OFFSET` on list endpoints
- [ ] Parameterized queries only — no string interpolation
- [ ] Soft delete queries filter `deleted_at IS NULL` where applicable

### 7. Observability

- [ ] Correct log levels: ERROR (immediate), WARNING (degraded), INFO (events), DEBUG (troubleshooting)
- [ ] No sensitive data in logs (passwords, tokens, emails)
- [ ] Meaningful error messages for debugging
- [ ] Background tasks log start and completion

### 8. Tests _(code mode only)_

- [ ] New logic has corresponding tests in `tests/`
- [ ] Tests cover happy path + error cases + edge cases
- [ ] Tests are deterministic (no external dependencies — uses SQLite in-memory)
- [ ] Test names describe behavior, not implementation
- [ ] Fixtures properly set up and torn down (function-scoped)
- [ ] `TestClient` used for endpoint tests
- [ ] DB dependency overridden in test fixtures

### 9. Project-Specific Rules _(plan mode primarily)_

#### Multi-Persona System
- [ ] Persona limit enforced (max 3 per user)
- [ ] Default persona always exists after registration
- [ ] Ownership checks go through persona → user chain
- [ ] Username uniqueness across all personas

#### Soft Delete
- [ ] `deleted_at` field used, not hard delete
- [ ] 30-day recovery window respected
- [ ] Soft-deleted users filtered from active queries
- [ ] 2FA email verification required for account deletion

#### Hobby & Search
- [ ] Tags processed correctly (comma-separated, lowercase)
- [ ] `HOBBY_SYNONYMS` in `core/config.py` updated if new categories added
- [ ] Image uploads use UUID filenames, old images cleaned up on update
- [ ] HTML descriptions sanitized via bleach

#### Email Verification
- [ ] Redis-based verification codes with 10-minute TTL
- [ ] 60-second cooldown between code sends
- [ ] Account inactive (`is_active=False`) until verified

### 10. Deploy Impact

- [ ] **Which Docker services change?** List affected services explicitly
- [ ] **Deploy order matters?** Dependencies between services documented
- [ ] **New env vars?** Added to `.env.example`
- [ ] **New migration?** Must run `alembic upgrade head` BEFORE deploying code that depends on it
- [ ] **Backwards compatible?** Can new code run against old DB schema during migration window?
- [ ] **Nginx changes?** `nginx/nginx.conf` updated if new routes/static paths added
- [ ] **New Python packages?** Added to `requirements.txt` with pinned version

### 11. Dependency Vulnerabilities

Run (or verify changes account for):
```bash
pip audit 2>/dev/null || pip-audit
```

- [ ] No new dependencies with known vulnerabilities
- [ ] New dependencies don't duplicate functionality of existing ones
- [ ] New dependencies are actively maintained
- [ ] Versions pinned in `requirements.txt`

### 12. Documentation Alignment

- [ ] Plan/code matches `CLAUDE.md` — no contradictions with project rules
- [ ] If changes affect behavior documented in `CONTRIBUTING.md`: doc update included
- [ ] If new endpoints: visible in Swagger UI (`/docs`)
- [ ] If migration changes: `CONTRIBUTING.md` migration guide still accurate

---

## UI Review Categories _(ui mode only)_

These categories are checked ONLY in UI mode (`/review ui`). They replace the code/plan categories above.

### U1. Mobile-First (P0)

- [ ] All touch targets >= 44px (iOS HIG) / 48dp (Material Design)
- [ ] No horizontal scroll on 320px viewport
- [ ] Font sizes: body >= 16px (prevents iOS zoom), headings scale proportionally
- [ ] Responsive breakpoints used correctly: Tailwind `sm:`, `md:`, `lg:`, `xl:`
- [ ] Mobile layout tested: stacked cards, collapsible sections
- [ ] No desktop-only features — all functionality accessible on mobile
- [ ] Images: responsive sizes, appropriate aspect ratios on mobile
- [ ] Modals/dialogs: full-screen on mobile, centered on desktop
- [ ] Forms usable on small screens (input sizes, button placement)

### U2. Accessibility (P1) — WCAG 2.2 AA

#### Color & Contrast
- [ ] Text contrast ratio >= 4.5:1 (normal text), >= 3:1 (large text 18px+/14px+ bold)
- [ ] UI element contrast >= 3:1 (borders, icons, focus indicators)
- [ ] Information not conveyed by color alone (add icons, text, patterns)

#### Keyboard Navigation
- [ ] Tab order logical (left-to-right, top-to-bottom)
- [ ] Enter/Space activate buttons and links
- [ ] Escape closes modals, dropdowns, panels
- [ ] Focus trap in modals (Tab cycles within, not behind)
- [ ] No keyboard traps — user can always Tab out

#### Screen Readers
- [ ] Heading hierarchy: h1 → h2 → h3 (no skipping levels)
- [ ] Landmarks: `<main>`, `<nav>`, `<aside>`, `<footer>`
- [ ] `aria-label` on icon buttons, images without text
- [ ] Form inputs have associated `<label>` or `aria-label`

#### Motion & Preferences
- [ ] `prefers-reduced-motion` respected — disable animations/transitions
- [ ] No auto-playing video/audio without user consent

### U3. Core Web Vitals (P2)

#### LCP < 2.5s
- [ ] Hero images optimized (compressed, correct format)
- [ ] No render-blocking resources in critical path
- [ ] Static assets served via Nginx (configured in `nginx/nginx.conf`)

#### CLS < 0.1
- [ ] All images have explicit `width` and `height` attributes
- [ ] No layout shifts from async content — use skeleton placeholders
- [ ] Dynamic content inserts below viewport or with `min-height`

#### INP < 200ms
- [ ] No blocking JS on user interactions
- [ ] Debounce/throttle heavy handlers (search, filter, scroll)
- [ ] Lazy load non-critical images and scripts

### U4. Nielsen's Heuristics + UX Laws (P3)

#### Nielsen's 10 Heuristics
1. **Visibility of system status** — loading states, progress indicators, feedback
2. **Match between system and real world** — hobby terminology users expect
3. **User control and freedom** — undo, back, close, cancel always available
4. **Consistency and standards** — same patterns across all pages (cards, forms)
5. **Error prevention** — confirmation for destructive actions (delete hobby/account), inline form validation
6. **Recognition over recall** — filter values visible, breadcrumbs where needed
7. **Flexibility and efficiency** — keyboard navigation for power users
8. **Aesthetic and minimalist design** — no information overload, progressive disclosure
9. **Help users recover from errors** — clear error messages with actionable next steps
10. **Help and documentation** — tooltips for non-obvious fields

#### UX Laws

| Law | Check | Action |
|-----|-------|--------|
| **Miller's Law (7±2)** | Are info groups > 9 items? | Break into sections, use tabs/accordions |
| **Fitts's Law** | Is primary CTA small or far from thumb zone? | Enlarge, move to bottom/center on mobile |
| **Hick's Law** | Too many choices at once? | Progressive disclosure, smart defaults |
| **Von Restorff Effect** | Does key info stand out? | Title, tags, CTA — visually distinct |
| **Aesthetic-Usability** | Does it look trustworthy? | Clean spacing, consistent typography |
| **Doherty Threshold** | Response within 400ms? | Skeleton screens, optimistic UI |
| **Peak-End Rule** | Does the flow end well? | Success states, confirmation messages |

### U5. Design System Compliance

#### Tailwind CSS Tokens
- [ ] Colors from Tailwind theme — no hardcoded hex/rgb values
- [ ] Spacing follows consistent scale (`p-2`, `p-4`, `gap-4`, etc.)
- [ ] Typography uses Tailwind classes (not arbitrary `text-[17px]`)
- [ ] Border radius consistent across components
- [ ] No inline styles — use Tailwind utility classes

#### Consistency
- [ ] Cards, buttons, forms styled consistently across all templates
- [ ] Same hover/focus states across interactive elements
- [ ] Error/success states follow same visual pattern
- [ ] Navigation consistent across all pages

#### Tailwind Best Practices
- [ ] No custom CSS unless absolutely necessary
- [ ] Responsive utilities used (`sm:`, `md:`, `lg:`) instead of media queries
- [ ] Dark mode support if applicable (`dark:` variants)
- [ ] No conflicting utility classes on same element

---

## Output Formats

### Code mode — small reviews (commit, wip, single file)

Print inline:

```markdown
## Code Review: [brief description]

**Scope:** [what was reviewed]
**Layers:** [api | services | core | models | templates]
**Categories checked:** [list or "all"]

### Findings

| # | Severity | Category | File | Line | Issue |
|---|----------|----------|------|------|-------|
| 1 | CRITICAL | Security | service.py | 42 | Description |
| 2 | HIGH | Correctness | auth.py | 100 | Description |

### Details

#### 1. CRITICAL: [Title]
**Category:** Security
**File:** `path/to/file.py:42`
**Issue:** [description]
**Fix:** [suggestion or code snippet]

### Summary
- **X** findings: Y CRITICAL, Z HIGH, W MEDIUM, V LOW
- Verdict: APPROVE / APPROVE WITH NOTES / REQUEST CHANGES
```

### Code mode — branch reviews (many commits)

Print inline AND save to `docs/reviews/review-{branch-name}.md`:

```markdown
# Code Review: [branch name]

**Branch:** `[name]`
**Base:** `main`
**Commits:** [count]
**Files changed:** [count]
**Layers:** [list]
**Categories checked:** [list or "all"]

## Features Reviewed

| # | Feature | Commits | Layers | Verdict |
|---|---------|---------|--------|---------|
| F1 | [name] | abc, def | API, Services | OK / Issues found |

## Findings

### CRITICAL
#### 1. [Title]
**Category:** Security
**File:** `path/to/file.py:42`
**Issue:** [description]
**Fix:** [code suggestion]

### HIGH
...

### MEDIUM
...

### LOW / INFO
...

## Passed Checks
- [x] Correctness: logic verified, edge cases handled
- [x] Security: OWASP checks passed
- [x] Architecture: layered architecture, SOLID/KISS/DRY consistent
- [x] Language: Python/FastAPI/SQLAlchemy checks passed
- [x] SQL: parameterized queries, indexes present
- [x] Observability: logging appropriate, no PII
- [x] Tests: adequate coverage
- [x] Dependencies: no known vulnerabilities
- [x] Docs: specs aligned
- [ ] N/A: [categories not applicable]

## Verdict
- [ ] **APPROVE** — no blockers, ready to merge
- [ ] **APPROVE WITH NOTES** — minor issues, can merge after addressing HIGH
- [ ] **REQUEST CHANGES** — must fix CRITICAL/HIGH before merge

Total: X findings (Y CRITICAL, Z HIGH, W MEDIUM, V LOW)
```

### Plan mode

Print inline. Modify plan file in-place if issues found.

```markdown
# Plan Review: [plan file name]

**Plan:** `[file path]`
**Layers affected:** [api | services | core | models | templates | migrations]
**Risk level:** Low | Medium | High
**Categories checked:** [list or "all"]
**Files consulted:** [list of source files read for context]

## Changes Made to Plan
1. **[Section]** — [what changed and why]

(If no changes: "No modifications needed.")

## Findings

### CRITICAL (must fix before implementing)
- **[Category:Check]** — description + fix applied

### HIGH (should fix)
- **[Category:Check]** — description + fix applied or recommendation

### MEDIUM (consider)
- **[Category:Check]** — suggestion

### LOW / INFO
- **[Category:Check]** — note

## Passed Checks
- [x] Completeness: context, files table, verification
- [x] Architecture: layered, SOLID/KISS/DRY consistent
- [x] Database: Alembic migration described
- [x] Security: OWASP checks passed
- [x] Language: Python/FastAPI/SQLAlchemy checks passed
- [x] Project rules: personas/soft-delete/search OK
- [x] Deploy: Docker services listed, migration order correct
- [x] Dependencies: no known vulnerabilities
- [x] Observability: logging plan present
- [x] Documentation: specs aligned
- [ ] N/A: [categories not applicable]

## Verdict
- [ ] **APPROVED** — plan is ready for implementation
- [ ] **APPROVED WITH NOTES** — implement after addressing HIGH items
- [ ] **CHANGES REQUIRED** — must fix CRITICAL items first

Total: X findings (Y CRITICAL, Z HIGH, W MEDIUM, V LOW)
```

### UI mode

Print inline AND save to `docs/reviews/ui-review-{target}.md`:

```markdown
# UI Review: [Page / Template name]

**Date:** YYYY-MM-DD
**Scope:** [template path / git scope]
**Categories audited:** [list or "all"]
**Files inspected:** [list of files read]

## Summary

| Category | Issues | P0 | P1 | P2 | P3 |
|----------|--------|----|----|----|----|
| Mobile-First | N | X | X | X | X |
| Accessibility | N | X | X | X | X |
| Core Web Vitals | N | X | X | X | X |
| UX Heuristics | N | X | X | X | X |
| Design System | N | X | X | X | X |
| **Total** | **N** | **X** | **X** | **X** | **X** |

## Critical Issues (P0)
1. **[Issue title]** — [Standard violated] — [Fix proposal]

## High Priority (P1)
1. **[Issue title]** — [Standard violated] — [Fix proposal]

## Medium Priority (P2)
1. **[Issue title]** — [Standard violated] — [Fix proposal]

## Low Priority (P3)
1. **[Issue title]** — [Standard violated] — [Fix proposal]

## Passed Checks
- [x] U1 Responsive: breakpoints correct, no overflow
- [x] U2 Accessibility: focus indicators, ARIA, keyboard
- [x] U3 Performance: optimized assets, no CLS
- [x] U4 UX: loading states, error prevention, consistency
- [x] U5 Design System: Tailwind tokens, consistent styling
- [ ] N/A: [checks not applicable]

## Verdict
- [ ] **APPROVE** — UI meets all standards
- [ ] **APPROVE WITH NOTES** — minor UX improvements suggested
- [ ] **REQUEST CHANGES** — accessibility or critical UX issues found

Total: X findings (Y CRITICAL, Z HIGH, W MEDIUM, V LOW)
```

**After UI findings:** Wait for user approval before generating an implementation plan.

---

## Constraints

- **Tailwind CSS only** — no custom CSS unless absolutely necessary
- **No new heavy dependencies** — keep bundle lean
- **Images** — optimize, use proper `width`/`height` attributes
- **Max upload size** — 10MB (enforced by Nginx)

## Rules

- Communicate in Russian
- **ALWAYS read all target files AND relevant source code before reviewing** — never speculate about code you haven't inspected
- Read project foundation (`CLAUDE.md`) before every review
- Be pragmatic: flag real issues that affect users, not theoretical concerns
- Every finding MUST reference the specific standard/guideline violated
- Provide actionable fix proposals with code snippets where possible
- In plan mode: modify the plan in-place if issues found, explain each change
- In UI mode: wait for user approval before generating implementation plan
- Do NOT implement fixes in code/UI mode — only review and propose
