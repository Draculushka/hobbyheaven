import nh3
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

from core.config import ALLOWED_ATTRS, ALLOWED_PROTOCOLS, ALLOWED_TAGS, TEMPLATES_DIR

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
    return Markup(cleaned)  # nosec B704


templates.env.filters['sanitize'] = sanitize_html
