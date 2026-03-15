from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    class Config:
        from_attributes = True

class HobbyBase(BaseModel):
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    image_path: Optional[str] = None

class HobbyCreate(HobbyBase):
    tags: List[str] = [] # Имена тегов

class HobbyUpdate(HobbyBase):
    tags: List[str] = []

class Hobby(HobbyBase):
    id: int
    created_at: datetime
    tags: List[Tag] = []

    class Config:
        from_attributes = True
