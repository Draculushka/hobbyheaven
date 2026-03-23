import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- S3 Object Storage ---
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = os.getenv("S3_BUCKET", "hobbyhold")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", "http://localhost:9000/hobbyhold")

ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'p', 'br', 'h2', 'h3', 'blockquote']
ALLOWED_ATTRS = {'a': ['href', 'title', 'target']}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

# --- Search Mapping ---
HOBBY_SYNONYMS = {
    "шахматы": ["chess", "шахматы"],
    "chess": ["chess", "шахматы"],
    "вархаммер": ["warhammer", "40k", "age of sigmar", "вархаммер"],
    "warhammer": ["warhammer", "40k", "age of sigmar", "вархаммер"],
    "40k": ["warhammer", "40k", "вархаммер"],
    "фотография": ["photo", "photography", "фото", "фотография"],
    "photo": ["photo", "photography", "фото", "фотография"],
    "photography": ["photo", "photography", "фото", "фотография"],
    "кулинария": ["cooking", "food", "еда", "кулинария"],
    "cooking": ["cooking", "food", "еда", "кулинария"],
    "йога": ["yoga", "йога"],
    "yoga": ["yoga", "йога"],
    "программирование": ["coding", "programming", "code", "программирование"],
    "programming": ["coding", "programming", "code", "программирование"],
    "coding": ["coding", "programming", "code", "программирование"]
}
