from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schemas.interaction import CommentResponse, ReactionResponse

class TagResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}

class PersonaResponse(BaseModel):
    id: int
    username: str
    bio: Optional[str] = None
    avatar_path: Optional[str] = None
    is_default: bool

    model_config = {"from_attributes": True}

class HobbyResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image_path: Optional[str] = None
    created_at: datetime
    author_persona: PersonaResponse
    tags: List[TagResponse] = []
    comments: List[CommentResponse] = []
    reactions: List[ReactionResponse] = []

    model_config = {"from_attributes": True}

class PaginatedHobbyResponse(BaseModel):
    items: List[HobbyResponse]
    total_pages: int
    current_page: int

class ErrorResponse(BaseModel):
    detail: str
