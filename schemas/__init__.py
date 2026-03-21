# TODO: integrate these schemas with API endpoints as response_model
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional

# --- Persona Schemas ---
class PersonaBase(BaseModel):
    username: str
    bio: Optional[str] = None
    avatar_path: Optional[str] = None

class PersonaCreate(PersonaBase):
    pass

class Persona(PersonaBase):
    id: int
    user_id: int
    is_default: bool

    model_config = ConfigDict(from_attributes=True)

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    username: str # Имя для первой (дефолтной) персоны
    password: str = Field(..., min_length=6, max_length=64)

class User(UserBase):
    id: int
    is_active: bool
    personas: list[Persona] = []

    model_config = ConfigDict(from_attributes=True)

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Tag Schemas ---
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

# --- Hobby Schemas ---
class HobbyBase(BaseModel):
    title: str
    description: Optional[str] = None
    image_path: Optional[str] = None

class HobbyCreate(HobbyBase):
    tags: list[str] = []
    persona_id: int # Обязательно указываем, от чьего имени постим

class HobbyUpdate(HobbyBase):
    tags: list[str] = []

class Hobby(HobbyBase):
    id: int
    persona_id: int
    created_at: datetime
    tags: list[Tag] = []
    author_persona: Optional[Persona] = None

    model_config = ConfigDict(from_attributes=True)
