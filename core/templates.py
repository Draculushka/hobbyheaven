import nh3
from markupsafe import Markup
from fastapi.templating import Jinja2Templates
from core.config import TEMPLATES_DIR, ALLOWED_TAGS, ALLOWED_ATTRS, ALLOWED_PROTOCOLS

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.autoescape = True


def sanitize_html(value: str) -> str:
    if not value:
        return ''
    cleaned = nh3.clean(
        str(value),
        tags=set(ALLOWED_TAGS),
        attributes={k: set(v) for k, v in ALLOWED_ATTRS.items()},
        url_schemes=set(ALLOWED_PROTOCOLS),
    )
    return Markup(cleaned)


templates.env.filters['sanitize'] = sanitize_html
