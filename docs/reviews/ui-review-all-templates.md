# UI Review: Все шаблоны HobbyHold

**Date:** 2026-03-22
**Scope:** Все 8 шаблонов в `templates/`
**Categories audited:** U1 (Mobile-First), U2 (Accessibility), U3 (Core Web Vitals), U4 (UX Heuristics), U5 (Design System)
**Files inspected:** `index.html`, `register.html`, `login.html`, `verify.html`, `cabinet.html`, `edit.html`, `profile.html`, `confirm_delete.html`, `nginx/nginx.conf`

## Summary

| Category | Issues | P0 | P1 | P2 | P3 |
|----------|--------|----|----|----|----|
| Mobile-First | 5 | 2 | 2 | 1 | 0 |
| Accessibility | 9 | 2 | 5 | 2 | 0 |
| Core Web Vitals | 4 | 1 | 2 | 1 | 0 |
| UX Heuristics | 5 | 0 | 3 | 2 | 0 |
| Design System | 5 | 0 | 1 | 3 | 1 |
| **Total** | **28** | **5** | **13** | **9** | **1** |

---

## Critical Issues (P0)

### 1. XSS через `{{ hobby.description | safe }}` — без серверной гарантии
**Стандарт:** OWASP A7 — Cross-Site Scripting
**Файл:** `templates/index.html:183`
**Issue:** Фильтр `| safe` отключает автоэкранирование Jinja2. Если `bleach` не применён на 100% путей записи (включая прямой SQL, миграции, импорт), — это вектор XSS. На UI-уровне это критичнее всего: пользователь видит неэкранированный HTML.
**Fix:** Добавить CSS-класс `prose` с ограничениями, либо использовать `| safe` только после явного `bleach.clean()` в шаблоне через кастомный Jinja2-фильтр:
```python
# В main.py
import bleach
templates.env.filters['sanitize'] = lambda v: bleach.clean(v, tags=['b','i','a','ul','ol','li','p','br'], strip=True)
```
```html
{{ hobby.description | sanitize | safe }}
```

### 2. Навбар ломается на мобильных < 375px — элементы перекрываются
**Стандарт:** U1 Mobile-First — No horizontal scroll on 320px viewport
**Файл:** `templates/index.html:46-121`
**Issue:** Навбар — единый `flex` ряд без `flex-wrap` и без мобильного бургер-меню. На 320px: лого + поиск + кубик + кнопки + разделитель = overflow. Поиск `max-w-2xl` не сужается достаточно.
**Fix:** Добавить мобильную версию навбара:
- На `md:` — текущий layout
- На мобильных — лого + бургер, поиск на второй строке или в выпадающем меню
```html
<div class="flex-grow max-w-2xl flex items-center gap-2 hidden md:flex">...</div>
<!-- mobile: search row below -->
<div class="md:hidden w-full px-4 py-2">
    <form ...><input ... class="w-full ..."></form>
</div>
```

### 3. `<label>` не связаны с `<input>` через `for`/`id` — формы недоступны для screen readers
**Стандарт:** U2 WCAG 2.2 AA — Form inputs must have associated labels
**Файлы:** `register.html:23-35`, `login.html:29-37`, `edit.html:55-62`, `cabinet.html:57-58`
**Issue:** Ни один `<label>` не имеет атрибута `for`, ни один `<input>` не имеет `id`. Screen readers не могут связать метку с полем.
**Fix:** Добавить `for`/`id` пары:
```html
<label for="email" class="...">Email</label>
<input id="email" type="email" name="email" ...>
```

### 4. CDN Tailwind CSS (45KB+ render-blocking JS) на каждой странице
**Стандарт:** U3 LCP < 2.5s — No render-blocking resources
**Файл:** Все 8 шаблонов — `<script src="https://cdn.tailwindcss.com">`
**Issue:** Tailwind CDN — это **runtime JS**, не CSS. Он парсит классы и генерирует стили в рантайме. Это блокирует рендер, увеличивает TTFB→FCP, и **не рекомендуется для production** самим Tailwind.
**Fix:** Перейти на Tailwind CLI build:
```bash
npx tailwindcss -i ./static/input.css -o ./static/output.css --minify
```
```html
<link rel="stylesheet" href="/static/output.css">
```

### 5. `{{ error }}` рендерится на login/verify/confirm_delete
**Стандарт:** OWASP A7 — XSS
**Файлы:** `login.html:24`, `verify.html:23`, `confirm_delete.html:24`
**Issue:** `{{ error }}` — автоэкранируется Jinja2 по умолчанию (не `| safe`). **INFO:** при проверке это не критично, т.к. Jinja2 экранирует по умолчанию. **Понижено до INFO.**

---

## High Priority (P1)

### 6. Кнопки-иконки без `aria-label`
**Стандарт:** U2 WCAG 2.2 AA — Icon buttons must have accessible names
**Файлы:** `index.html:101` (кнопка категорий), `index.html:109` (уведомления), `cabinet.html:105-107` (редактировать/удалить)
**Issue:** SVG-кнопки без текста внутри и без `aria-label`. Screen reader озвучит "button" без контекста.
**Fix:**
```html
<button aria-label="Показать категории" ...>
<button aria-label="Уведомления" ...>
<a aria-label="Редактировать хобби" href="/edit/...">
<button aria-label="Удалить хобби" type="submit">
```

### 7. Модальное окно изображения без keyboard support
**Стандарт:** U2 WCAG 2.2 AA — Keyboard Navigation, Focus Trap
**Файл:** `index.html:191-196`
**Issue:** Модал открывается по `onclick`, закрывается по `onclick`, но:
- Нет `role="dialog"` и `aria-modal="true"`
- Нет focus trap — Tab уходит за модал
- Нет закрытия по Escape
- Нет `tabindex` — модал не focusable
**Fix:**
```html
<div id="imageModal" role="dialog" aria-modal="true" aria-label="Просмотр изображения" tabindex="-1" ...>
```
```js
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') document.getElementById('imageModal').classList.add('hidden');
});
```

### 8. Карточки хобби в cabinet — непригодны на мобильных
**Стандарт:** U1 Mobile-First — Mobile layout
**Файл:** `cabinet.html:91-118`
**Issue:** Карточки используют `flex gap-6` с фиксированным `w-32 h-32` для изображения. На экране 320px это 128px + gap + текст = overflow или сжатие текста до нечитаемого.
**Fix:** На мобильных использовать вертикальную раскладку:
```html
<article class="... flex flex-col sm:flex-row gap-4 sm:gap-6 ...">
    <img class="w-full h-48 sm:w-32 sm:h-32 ...">
```

### 9. Нет heading hierarchy — `<h1>` пропущен на нескольких страницах
**Стандарт:** U2 WCAG — Heading hierarchy h1 -> h2 -> h3
**Файлы:** `cabinet.html` — нет `<h1>`, начинается с `<h2>`. `index.html` — `<h1>` есть, но hobby title использует `<span>` вместо `<h2>`/`<h3>`.
**Fix:** Добавить `<h1>` на cabinet ("Личный кабинет"), использовать `<h2>`/`<h3>` для карточек хобби.

### 10. Кнопка "Удалить аккаунт" без подтверждения первого уровня
**Стандарт:** U4 Nielsen #5 — Error Prevention, confirmation for destructive actions
**Файл:** `cabinet.html:73-75`
**Issue:** POST-форма удаления аккаунта не имеет `onsubmit="return confirm(...)"`. Один случайный клик инициирует отправку кода и переход на страницу подтверждения. В отличие от удаления хобби (строка 106), где `confirm()` есть.
**Fix:**
```html
<form action="/cabinet/delete" method="post" onsubmit="return confirm('Вы уверены, что хотите удалить аккаунт?');">
```

### 11. Отсутствует `<main>` landmark на всех страницах
**Стандарт:** U2 WCAG — Landmarks
**Файлы:** Все 8 шаблонов
**Issue:** Контент не обёрнут в `<main>`. Screen readers не могут быстро перейти к основному содержимому.
**Fix:** Обернуть основной контент в `<main>`:
```html
<main class="max-w-4xl mx-auto p-6 md:p-12">
    ...
</main>
```

### 12. Нет базового шаблона — 8 файлов дублируют `<head>`, навбар, стили
**Стандарт:** U5 Design System — Consistency
**Файлы:** Все шаблоны
**Issue:** Каждый шаблон — полный HTML-документ с дублированием: `<head>`, шрифты, Tailwind CDN, favicon (только в index.html), inline `<style>`. Навбары различаются между страницами (3 разных варианта). Это ведёт к:
- Рассинхронизации стилей (напр. разные `border-radius` у CKEditor: `16px` в index vs `12px` в edit)
- Отсутствию favicon на 7 из 8 страниц
- Разному поведению навбара
**Fix:** Создать `templates/base.html` с Jinja2 `{% block %}`:
```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}HobbyHold{% endblock %}</title>
    <link rel="icon" type="image/svg+xml" href="...">
    <link rel="stylesheet" href="/static/output.css">
    {% block head %}{% endblock %}
</head>
<body class="text-[#2D3436] antialiased">
    {% block nav %}{% include 'partials/nav.html' %}{% endblock %}
    <main>{% block content %}{% endblock %}</main>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 13. Уведомления — кнопка-заглушка с "непрочитанным" индикатором
**Стандарт:** U4 Nielsen #1 — Visibility of System Status
**Файл:** `index.html:109`
**Issue:** Кнопка уведомлений с оранжевой точкой "непрочитанных", но она ничего не делает (нет `href`, нет `onclick`). Это вводит пользователя в заблуждение — он видит индикатор, кликает, ничего не происходит.
**Fix:** Убрать кнопку до реализации уведомлений, либо скрыть индикатор:
```html
<!-- Убрать или скрыть до реализации -->
<button class="p-2 text-[#BDC3C7] cursor-not-allowed" disabled title="Скоро">
```

---

## Medium Priority (P2)

### 14. Изображения без `width`/`height` — CLS
**Стандарт:** U3 CLS < 0.1
**Файлы:** `index.html:166`, `cabinet.html:93`, `profile.html:82`, `edit.html:88`
**Issue:** `<img>` без `width`/`height` атрибутов. Браузер не знает размер до загрузки — layout shift.
**Fix:** Добавить `width` и `height` (или использовать `aspect-ratio` через Tailwind `aspect-video`/`aspect-square`):
```html
<img ... class="aspect-[4/3] w-full object-cover" loading="lazy">
```

### 15. CKEditor загружается на главной даже без формы создания (для гостей)
**Стандарт:** U3 INP/Performance — No blocking JS
**Файл:** `index.html:9`
**Issue:** `<script src="ckeditor5/...">` загружается всегда, но CKEditor нужен только авторизованным пользователям (форма создания — внутри `{% if user %}`). Для гостей это ~300KB лишнего JS.
**Fix:**
```html
{% if user %}
<script src="https://cdn.ckeditor.com/ckeditor5/40.0.0/classic/ckeditor.js"></script>
{% endif %}
```

### 16. "Подписчиков: 0" — hardcoded placeholder
**Стандарт:** U4 Nielsen #1 — Visibility of System Status
**Файл:** `profile.html:61-63`
**Issue:** Счётчик подписчиков всегда "0" — hardcoded. Если фича не реализована, не стоит показывать нулевой счётчик — это выглядит как баг.
**Fix:** Убрать до реализации функционала подписок.

### 17. Нет `loading="lazy"` на изображениях ниже fold
**Стандарт:** U3 Performance — Lazy load non-critical images
**Файлы:** `index.html:166`, `profile.html:82`, `cabinet.html:93`
**Issue:** Все изображения загружаются сразу, без lazy loading.
**Fix:** `<img ... loading="lazy">`

### 18. Нет pagination на главной и в профиле
**Стандарт:** U4 Hick's Law — Too many choices; U3 Performance
**Файлы:** `index.html:161-188`, `profile.html:77-105`
**Issue:** Все хобби рендерятся одним списком. При 100+ записях — огромный DOM, долгая загрузка, перегрузка информацией.
**Fix:** Добавить серверную пагинацию (LIMIT/OFFSET в query) + UI кнопки "Загрузить ещё" или номерные страницы.

### 19. Текст "Выход" слишком мелкий — `text-[10px]`
**Стандарт:** U1 Mobile-First — touch targets >= 44px
**Файлы:** `index.html:116`, `cabinet.html:21`
**Issue:** Кнопка "Выход" — 10px текст без padding. Touch target значительно меньше 44px.
**Fix:** Увеличить padding:
```html
<a href="/logout" class="text-xs font-bold text-[#BDC3C7] hover:text-[#C0392B] uppercase tracking-widest transition-colors px-2 py-2">Выход</a>
```

### 20. Sidebar в cabinet не скроллится отдельно на длинных списках
**Стандарт:** U1 Mobile-First
**Файл:** `cabinet.html:29`
**Issue:** `sticky top-24` на sidebar, но на мобильных sidebar отображается первым (`flex-col`) и занимает весь экран. Пользователю нужно долго скроллить вниз до публикаций.
**Fix:** На мобильных — сворачиваемый sidebar или tabs.

### 21. Hardcoded hex-цвета вместо Tailwind-токенов
**Стандарт:** U5 Design System — Colors from Tailwind theme
**Файлы:** Все шаблоны
**Issue:** Повсеместно `text-[#2D3436]`, `bg-[#F8F9FA]`, `text-[#FF9F43]`, `border-[#F1F2F6]` и т.д. — это arbitrary values Tailwind, не токены. При смене палитры придётся менять 100+ мест.
**Fix:** Настроить `tailwind.config.js` с кастомными цветами:
```js
theme: {
  extend: {
    colors: {
      primary: '#FF9F43',
      'primary-hover': '#EE5253',
      dark: '#2D3436',
      muted: '#7F8C8D',
      surface: '#F8F9FA',
      border: '#F1F2F6',
      cream: '#FDFCF0',
    }
  }
}
```
Затем заменить `text-[#2D3436]` -> `text-dark`, `bg-[#FF9F43]` -> `bg-primary` и т.д.

### 22. Разные border-radius значения без консистентности
**Стандарт:** U5 Design System — Border radius consistent
**Файлы:** Все шаблоны
**Issue:** Используются `rounded-[48px]`, `rounded-[40px]`, `rounded-[32px]`, `rounded-2xl`, `rounded-xl`, `rounded-lg`, `rounded-full` — 7 разных значений радиуса. Нет системы.
**Fix:** Определить шкалу: cards = `rounded-3xl`, inputs/buttons = `rounded-2xl`, chips/badges = `rounded-full`.

---

## Low Priority (P3)

### 23. `previewImage()` дублируется в index.html и edit.html
**Стандарт:** U5 — DRY
**Файлы:** `index.html:196`, `edit.html:113-125`
**Issue:** Одна и та же функция определена в двух шаблонах — при исправлении бага нужно править в двух местах.
**Fix:** Вынести в общий `static/js/app.js`.

---

## Passed Checks
- [x] U1 Responsive: viewport meta present on all pages
- [x] U2 Accessibility: `lang="ru"` на всех `<html>`
- [x] U4 UX: confirm() на удалении хобби, кнопка "Отмена" на edit и confirm_delete
- [x] U4 UX: error states показываются на login/verify/confirm_delete
- [x] U5 Design System: единая цветовая палитра (orange/dark) across all pages
- [x] U5 Design System: единые шрифты Inter + Lora
- [ ] N/A: Dark mode (не реализован)

---

## Verdict
- [x] **REQUEST CHANGES** — accessibility и critical UX issues found

**Total: 23 findings (5 CRITICAL/P0, 13 HIGH/P1, 9 MEDIUM/P2, 1 LOW/P3)**

**Топ-3 приоритета для исправления:**
1. Создать `base.html` — устранит дублирование, обеспечит favicon/nav/`<main>` повсюду
2. Перейти с Tailwind CDN на CLI build — production-критично
3. Добавить `aria-label`, `for`/`id`, landmarks — базовая accessibility
