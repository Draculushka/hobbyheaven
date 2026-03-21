import bleach
from markupsafe import Markup
from fastapi.templating import Jinja2Templates
from core.config import TEMPLATES_DIR, ALLOWED_TAGS, ALLOWED_ATTRS, ALLOWED_PROTOCOLS

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def sanitize_html(value: str) -> str:
    if not value:
        return ''
    cleaned = bleach.clean(str(value), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=ALLOWED_PROTOCOLS, strip=True)
    return Markup(cleaned)


templates.env.filters['sanitize'] = sanitize_html
