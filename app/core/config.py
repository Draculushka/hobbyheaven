import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "templates"

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

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
