from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class CommentBase(BaseModel):
    text: str = Field(..., max_length=1000)

class CommentCreate(CommentBase):
    persona_id: Optional[int] = None

class CommentUpdate(CommentBase):
    pass

class CommentReactionResponse(BaseModel):
    id: int
    comment_id: int
    persona_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class CommentResponse(CommentBase):
    id: int
    hobby_id: int
    persona_id: int
    created_at: datetime
    reactions: list[CommentReactionResponse] = []

    model_config = {"from_attributes": True}

class ReactionBase(BaseModel):
    emoji_type: str = Field(default="heart", max_length=50)

class ReactionCreate(ReactionBase):
    pass

class ReactionResponse(ReactionBase):
    id: int
    hobby_id: int
    persona_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
