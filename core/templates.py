import bleach
from markupsafe import Markup
from fastapi.templating import Jinja2Templates
from core.config import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'p', 'br', 'h2', 'h3', 'blockquote']
ALLOWED_ATTRS = {'a': ['href', 'title', 'target']}


def sanitize_html(value: str) -> str:
    if not value:
        return ''
    cleaned = bleach.clean(str(value), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return Markup(cleaned)


templates.env.filters['sanitize'] = sanitize_html
