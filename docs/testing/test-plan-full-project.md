# Test Plan: HobbyHold — Полный проект

**Date:** 2026-03-22
**Scope:** Весь проект (все слои)
**Base commit:** `06d0c20` (branch `fix/review`)
**Layers:** API Endpoints, Services, Core, Models, Templates
**Existing tests:** 17 (tests/test_main.py)

---

## Test Plan Summary

| Priority | New Tests | Already Covered | Total |
|----------|-----------|-----------------|-------|
| P0       | 30        | 8               | 38    |
| P1       | 82        | 7               | 89    |
| P2       | 87        | 0               | 87    |
| P3       | 22        | 0               | 22    |
| **Total**| **221**   | **15**          | **236**|

### Existing Test Coverage

| Test file | Tests | Covers |
|-----------|-------|--------|
| `tests/test_main.py` | 17 | Рендер страниц (register, login, home), регистрация (success, dup email, dup username), логин (invalid creds, unverified), пагинация, поиск, unauth CRUD, logout, random, profile 404, cabinet unauth |

### Files to create:
- `tests/test_auth_service.py` (NEW) — 26 тестов
- `tests/test_hobby_service.py` (NEW) — 52 теста
- `tests/test_security.py` (NEW) — 16 тестов
- `tests/test_models.py` (NEW) — 20 тестов
- `tests/test_templates_filter.py` (NEW) — 7 тестов
- `tests/test_endpoints_auth.py` (NEW) — 38 тестов
- `tests/test_endpoints_hobbies.py` (NEW) — 32 теста
- `tests/test_endpoints_profile.py` (NEW) — 30 тестов

### Verification Checklist:
- [ ] `SECRET_KEY=test DATABASE_URL=sqlite:// PYTHONPATH=. pytest tests/ -v`

---

## Обнаруженные потенциальные дефекты

| # | Расположение | Описание | Severity |
|---|-------------|----------|----------|
| BUG-1 | `services/auth_service.py` | `authenticate_user` НЕ фильтрует soft-deleted пользователей. Фильтрация есть только в `get_current_user`. Soft-deleted user может залогиниться | P1 |
| BUG-2 | `services/hobby_service.py` | `search_hobbies`: при `page=0` → `offset=-limit` (невалидный). При `limit=0` → `ZeroDivisionError` | P1 |
| BUG-3 | `services/hobby_service.py` | `process_tags`: "tag1, tag1" не дедуплицируется → возможны дублирующиеся M2M связи | P2 |

---

## ЧАСТЬ 1: API Endpoints (auth.py)

### GET /register

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-A01 | Integration | EP | GET /register → 200, форма | P2 | COVERED |
| TP-A02 | Integration | EP | GET /register?error=msg → ошибка в контексте | P3 | TODO |

### POST /register

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-A03 | Integration | EP | Успешная регистрация → User+Persona, редирект /verify-email | P0 | COVERED |
| TP-A04 | Integration | EP | Дублирующий email → редирект с ошибкой | P0 | COVERED |
| TP-A05 | Integration | EP | Дублирующий username → редирект с ошибкой | P0 | COVERED |
| TP-A06 | Integration | BVA | Пароль 5 символов (< min=6) → 422 | P1 | TODO |
| TP-A07 | Integration | BVA | Пароль 6 символов (граница min) → успех | P1 | TODO |
| TP-A08 | Integration | BVA | Пароль 64 символа (граница max) → успех | P1 | TODO |
| TP-A09 | Integration | BVA | Пароль 65 символов (> max=64) → 422 | P1 | TODO |
| TP-A10 | Integration | EP | Пустой username → 422 | P2 | TODO |
| TP-A11 | Integration | EP | Пустой email → 422 | P2 | TODO |
| TP-A12 | Integration | EG | Email без @ → проверить поведение | P2 | TODO |
| TP-A13 | Integration | EG | Username с SQL-инъекцией → безопасно | P2 | TODO |
| TP-A14 | Integration | EG | Username с XSS → экранирование | P2 | TODO |

### POST /verify-email

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-A15 | Integration | EP | Верный код → 303 на /, cookie установлен | P0 | TODO |
| TP-A16 | Integration | EP | Неверный код → редирект с ошибкой | P0 | TODO |
| TP-A17 | Integration | ST | Просроченный код (TTL) → ошибка | P1 | TODO |
| TP-A18 | Integration | BVA | 5-я неудачная попытка → код блокируется | P1 | TODO |
| TP-A19 | Unit | EG | Cookie: httponly=True, secure=True, samesite=lax | P1 | TODO |

### POST /login

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-A20 | Integration | EP | Валидные credentials → 303 /, cookie | P0 | TODO |
| TP-A21 | Integration | EP | Неверный пароль → редирект с ошибкой | P0 | COVERED |
| TP-A22 | Integration | ST | Неактивный пользователь → /verify-email | P0 | COVERED |
| TP-A23 | Integration | DT | Soft-deleted пользователь → ошибка "в процессе удаления" | P0 | TODO |
| TP-A24 | Integration | EG | Несуществующий email → тот же ответ что неверный пароль (no info leak) | P1 | TODO |
| TP-A25 | Unit | EG | Cookie flags: httponly, secure, samesite | P1 | TODO |

### GET /logout

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-A26 | Integration | EP | Logout → cookie удалён, 303 / | P1 | COVERED |
| TP-A27 | Integration | EG | Logout без cookie → 303 / (не падает) | P2 | TODO |

---

## ЧАСТЬ 2: API Endpoints (hobbies.py)

### GET /

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-H01 | Integration | EP | GET / → 200, список хобби | P0 | COVERED |
| TP-H02 | Integration | EP | GET /?search=keyword → фильтрация | P0 | COVERED |
| TP-H03 | Integration | EP | GET /?page=1 → пагинация | P1 | COVERED |
| TP-H04 | Integration | BVA | GET /?page=0 → проверить поведение | P2 | TODO |
| TP-H05 | Integration | BVA | GET /?page=-1 → невалидная страница | P2 | TODO |
| TP-H06 | Integration | BVA | GET /?page=999999 → пустой результат | P2 | TODO |
| TP-H07 | Integration | EG | GET /?search=\<script\> → XSS безопасность | P1 | TODO |
| TP-H08 | Integration | EG | GET /?page=abc → 422 | P2 | TODO |

### GET /random

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-H09 | Integration | EP | Пустая БД → редирект / | P2 | COVERED |
| TP-H10 | Integration | EP | Есть хобби → 303 /?search=\<title\> | P2 | TODO |

### POST /create-hobby

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-H11 | Integration | EP | Без auth → /login | P0 | COVERED |
| TP-H12 | Integration | EP | С auth, без persona_id → дефолтная персона | P0 | TODO |
| TP-H13 | Integration | EP | С auth + своя persona_id → создание | P1 | TODO |
| TP-H14 | Integration | DT | IDOR: чужая persona_id → 403 | P0 | TODO |
| TP-H15 | Integration | EP | Нет персоны → 400 | P1 | TODO |
| TP-H16 | Integration | BVA | title 255 символов → успех | P2 | TODO |
| TP-H17 | Integration | BVA | title 256 символов → ошибка/обрезка | P2 | TODO |

### GET /edit/{hobby_id}

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-H18 | Integration | EP | Без auth → /login | P0 | COVERED |
| TP-H19 | Integration | EP | Своё хобби → 200, форма | P1 | TODO |
| TP-H20 | Integration | DT | IDOR: чужое хобби → 403 | P0 | TODO |
| TP-H21 | Integration | EP | Несуществующее → 404 | P1 | TODO |

### POST /update/{hobby_id}

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-H22 | Integration | EP | Без auth → /login | P0 | TODO |
| TP-H23 | Integration | EP | Своё хобби → обновление, 303 | P0 | TODO |
| TP-H24 | Integration | DT | IDOR: чужое хобби → 403 | P0 | TODO |

### POST /delete-hobby/{hobby_id}

**Decision Table:**

| auth | exists | owner | admin | Result |
|------|--------|-------|-------|--------|
| No | - | - | - | 401 |
| Yes | No | - | - | 404 |
| Yes | Yes | Yes | No | 303 |
| Yes | Yes | No | Yes | 303 |
| Yes | Yes | No | No | 403 |

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-H25 | Integration | EP | Без auth → 401 | P0 | COVERED |
| TP-H26 | Integration | EP | Своё хобби → удаление, 303 | P0 | TODO |
| TP-H27 | Integration | DT | IDOR: чужое хобби (не admin) → 403 | P0 | TODO |
| TP-H28 | Integration | DT | Admin удаляет чужое → 303 | P0 | TODO |
| TP-H29 | Integration | EP | Несуществующее → 404 | P1 | TODO |

---

## ЧАСТЬ 3: API Endpoints (profile.py)

### GET /cabinet

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-P01 | Integration | EP | Без auth → /login | P0 | COVERED |
| TP-P02 | Integration | EP | С auth → 200, персоны и хобби | P0 | TODO |

### POST /cabinet/persona/create

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-P03 | Integration | EP | Без auth → 401 | P0 | TODO |
| TP-P04 | Integration | EP | Создание 2-й персоны → успех | P0 | TODO |
| TP-P05 | Integration | BVA | 3-я персона (граница) → успех | P1 | TODO |
| TP-P06 | Integration | BVA | 4-я персона (> лимита 3) → 400 | P0 | TODO |
| TP-P07 | Integration | EP | Дублирующий username → 400 | P1 | TODO |
| TP-P08 | Integration | EP | С аватаром → avatar_path сохранён | P2 | TODO |

### POST /cabinet/delete + confirm

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-P09 | Integration | EP | Запрос удаления → 303 /cabinet/delete/confirm | P0 | TODO |
| TP-P10 | Integration | EP | Верный код → soft delete, cookie удалён | P0 | TODO |
| TP-P11 | Integration | EP | Неверный код → ошибка | P0 | TODO |
| TP-P12 | Integration | ST | После soft-delete: логин → ошибка | P0 | TODO |
| TP-P13 | Integration | ST | После soft-delete: JWT → get_current_user = None | P0 | TODO |

### GET /profile/{username}

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-P14 | Integration | EP | Несуществующий → 404 | P1 | COVERED |
| TP-P15 | Integration | EP | Существующий → 200, персона и хобби | P1 | TODO |
| TP-P16 | Integration | EP | Профиль без хобби → 200, пустой список | P2 | TODO |

---

## ЧАСТЬ 4: core/security.py

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-S01 | Unit | EP | create_access_token → валидный JWT с sub и exp | P0 | TODO |
| TP-S02 | Unit | EP | verify_password(correct) → True | P0 | TODO |
| TP-S03 | Unit | EP | verify_password(wrong) → False | P0 | TODO |
| TP-S04 | Unit | EP | get_password_hash → bcrypt hash ($2b$) | P1 | TODO |
| TP-S05 | Unit | EP | get_current_user: нет cookie → None | P0 | TODO |
| TP-S06 | Unit | EP | get_current_user: валидный JWT → User | P0 | TODO |
| TP-S07 | Unit | EP | get_current_user: истекший JWT → None | P0 | TODO |
| TP-S08 | Unit | EP | get_current_user: невалидная подпись → None | P0 | TODO |
| TP-S09 | Unit | EG | get_current_user: JWT без "sub" → None | P1 | TODO |
| TP-S10 | Unit | DT | get_current_user: deleted_at != None → None | P0 | TODO |
| TP-S11 | Unit | DT | get_current_user: is_active == False → None | P0 | TODO |

---

## ЧАСТЬ 5: services/auth_service.py

### create_user

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-AS01 | Unit | EP | Валидные данные → User + дефолтная Persona | P1 | TODO |
| TP-AS02 | Unit | EG | Дублирующий email → IntegrityError | P1 | TODO |
| TP-AS03 | Unit | ST | Новый User.is_active == False | P1 | TODO |
| TP-AS04 | Unit | DA | Пароль хэшируется (hashed_password != password) | P2 | TODO |
| TP-AS05 | Unit | EG | flush() даёт user.id до commit → Persona.user_id корректен | P2 | TODO |

### authenticate_user

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-AS06 | Unit | DT | Верный email+пароль → User | P1 | TODO |
| TP-AS07 | Unit | DT | Верный email+неверный пароль → None | P1 | TODO |
| TP-AS08 | Unit | DT | Несуществующий email → None | P1 | TODO |
| TP-AS09 | Unit | EG | Soft-deleted пользователь → авторизация проходит (BUG-1) | P1 | TODO |

### request_verification_code

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-AS10 | Unit | ST | Первый запрос → 6-значный код, setex 600s | P1 | TODO |
| TP-AS11 | Unit | ST | Повторный запрос в cooldown → None | P1 | TODO |
| TP-AS12 | Unit | BVA | Код всегда 100000–999999 | P1 | TODO |
| TP-AS13 | Unit | EG | Redis недоступен → ConnectionError | P2 | TODO |

### verify_code

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-AS14 | Unit | DT | Верный код → is_active=True, keys deleted, True | P1 | TODO |
| TP-AS15 | Unit | DT | Неверный код → attempts+1, False | P1 | TODO |
| TP-AS16 | Unit | BVA | 5-я попытка → блокировка, keys deleted | P1 | TODO |
| TP-AS17 | Unit | ST | Код истёк (TTL) → stored=None → False | P1 | TODO |
| TP-AS18 | Unit | EG | Пользователь не найден → False | P2 | TODO |

---

## ЧАСТЬ 6: services/hobby_service.py

### sanitize_description

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-HS01 | Unit | EP | Обычный текст → без изменений | P1 | TODO |
| TP-HS02 | Unit | EP | \<b\>, \<i\>, \<a\> (разрешённые) → сохраняются | P1 | TODO |
| TP-HS03 | Unit | EP | \<script\>, \<iframe\> (запрещённые) → strip | P1 | TODO |
| TP-HS04 | Unit | DA | \<a href="javascript:..."\> → протокол удалён | P0 | TODO |
| TP-HS05 | Unit | EG | \<img onerror="alert(1)"\> → удалён | P1 | TODO |
| TP-HS06 | Unit | BVA | Пустая строка → пустая строка | P2 | TODO |

### save_upload_image

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-HS07 | Unit | EP | None → None | P1 | TODO |
| TP-HS08 | Unit | EP | Валидный .jpg → UUID имя, сохранён | P1 | TODO |
| TP-HS09 | Unit | EP | .exe → HTTPException 400 | P0 | TODO |
| TP-HS10 | Unit | BVA | Файл ровно 5MB → принят | P1 | TODO |
| TP-HS11 | Unit | BVA | Файл 5MB+1 → HTTPException 400 | P1 | TODO |
| TP-HS12 | Unit | EG | .JPG (верхний регистр) → .lower() → принят | P2 | TODO |
| TP-HS13 | Unit | EG | "../../../etc/passwd.jpg" → UUID заменяет имя | P2 | TODO |

**Sub-scenarios расширений (EP):**

| Расширение | Ожидание |
|------------|----------|
| `.jpg` | Принят |
| `.jpeg` | Принят |
| `.png` | Принят |
| `.gif` | Принят |
| `.webp` | Принят |
| `.exe` | 400 |
| `.svg` | 400 |
| `.php` | 400 |
| (без расширения) | 400 |

### search_hobbies

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-HS14 | Unit | EP | search="" → все хобби | P1 | TODO |
| TP-HS15 | Unit | EP | search="chess" → синонимы ["chess","шахматы"] | P1 | TODO |
| TP-HS16 | Unit | DA | LIKE escaping: "%" → "\%" | P0 | TODO |
| TP-HS17 | Unit | DA | LIKE escaping: "_" → "\_" | P0 | TODO |
| TP-HS18 | Unit | BVA | page=1, total=0 → total_pages=1, пустой список | P1 | TODO |
| TP-HS19 | Unit | BVA | page=1, total=11, limit=10 → total_pages=2 | P2 | TODO |
| TP-HS20 | Unit | EG | Soft-deleted user → его хобби исключены | P1 | TODO |

### create_hobby / update_hobby / delete_hobby

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-HS21 | Unit | EP | create_hobby: description sanitized | P1 | TODO |
| TP-HS22 | Unit | EP | create_hobby: tags "tag1, tag2" → 2 Tag + M2M | P1 | TODO |
| TP-HS23 | Unit | EP | update_hobby: новое изображение → старое удаляется | P1 | TODO |
| TP-HS24 | Unit | EP | delete_hobby: файл + запись удаляются | P1 | TODO |
| TP-HS25 | Unit | EG | delete_hobby: файл не на диске → не падает | P2 | TODO |

### process_tags

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-HS26 | Unit | EP | Пустая строка → [] | P2 | TODO |
| TP-HS27 | Unit | EP | "tag1, tag2" → [Tag, Tag] | P1 | TODO |
| TP-HS28 | Unit | EP | Существующий тег → не дублируется | P1 | TODO |
| TP-HS29 | Unit | BVA | "  ,  , " → [] (strip + filter) | P2 | TODO |

---

## ЧАСТЬ 7: core/templates.py — sanitize_html

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-T01 | Unit | EP | None → '' | P1 | TODO |
| TP-T02 | Unit | EP | Обычный текст → Markup(текст) | P1 | TODO |
| TP-T03 | Unit | EP | \<script\> → strip, Markup | P0 | TODO |
| TP-T04 | Unit | DA | javascript: в href → удалён | P0 | TODO |
| TP-T05 | Unit | DA | Возвращает markupsafe.Markup | P2 | TODO |

---

## ЧАСТЬ 8: models/__init__.py

| Test ID | Type | Technique | Description | Priority | Status |
|---------|------|-----------|-------------|----------|--------|
| TP-M01 | Unit | ST | User lifecycle: created → verified → soft-deleted | P1 | TODO |
| TP-M02 | Unit | DA | User.email: unique=True | P1 | TODO |
| TP-M03 | Unit | DA | User.is_admin: default=False (Boolean) | P2 | TODO |
| TP-M04 | Unit | DA | User.is_active: default=False | P1 | TODO |
| TP-M05 | Unit | DA | Persona.username: unique=True | P1 | TODO |
| TP-M06 | Unit | DA | Hobby.title: String(255) | P2 | TODO |
| TP-M07 | Unit | DA | Hobby.tags: M2M через hobby_tags | P1 | TODO |
| TP-M08 | Unit | DA | Tag.name: unique=True | P1 | TODO |
| TP-M09 | Unit | EG | Cascade delete: User → Personas | P1 | TODO |

---

## ЧАСТЬ 9: Cross-Cutting Tests

| # | Trigger | Test case | Priority | Status |
|---|---------|-----------|----------|--------|
| S-01 | Access Control | IDOR: user A не может редактировать hobby user B | P0 | TODO |
| S-02 | Access Control | IDOR: user A не может удалить hobby user B | P0 | TODO |
| S-03 | Access Control | IDOR: user A не может создать hobby от persona user B | P0 | TODO |
| S-04 | Access Control | Admin может удалить чужое hobby | P0 | TODO |
| S-05 | Access Control | Soft-deleted user не может аутентифицироваться через JWT | P0 | TODO |
| S-06 | Input Validation | SQL injection в search → безопасно (SQLAlchemy) | P1 | TODO |
| S-07 | Input Validation | LIKE injection: % и _ экранируются | P0 | TODO |
| S-08 | Input Validation | XSS в description → bleach strip | P0 | TODO |
| S-09 | Input Validation | javascript: в href → blocked | P0 | TODO |
| S-10 | File Upload | .exe → rejected | P0 | TODO |
| S-11 | File Upload | >5MB → rejected | P0 | TODO |
| S-12 | Auth | Expired JWT → None | P0 | TODO |
| S-13 | Auth | Brute-force verification code → blocked after 5 | P0 | TODO |
| S-14 | Auth | Cookie: httponly, secure, samesite | P1 | TODO |
| S-15 | State | Full registration flow: register → verify → login → create hobby | P1 | TODO |
| S-16 | State | Full deletion flow: request code → confirm → soft delete → login fails | P1 | TODO |
| S-17 | State | Persona limit: cannot create 4th | P0 | TODO |

---

## Рекомендуемый порядок реализации

### Спринт 1: P0 (30 тестов)
Фокус: IDOR, auth bypass, XSS, file upload, soft-delete
- `test_security.py`: TP-S01, S02, S03, S05-S08, S10, S11
- `test_endpoints_hobbies.py`: TP-H12, H14, H20, H23, H24, H27, H28
- `test_endpoints_profile.py`: TP-P03, P04, P06, P09-P13
- `test_endpoints_auth.py`: TP-A15, A16, A20, A23
- `test_hobby_service.py`: TP-HS04, HS09, HS16, HS17
- `test_templates_filter.py`: TP-T03, T04

### Спринт 2: P1 (82 теста)
Фокус: BVA, JWT edge cases, cookie flags, service unit tests
- Все unit-тесты сервисов (auth_service, hobby_service)
- Все модельные тесты
- Остальные integration-тесты

### Спринт 3: P2-P3 (109 тестов)
Фокус: edge cases, cosmetic, пустые состояния
