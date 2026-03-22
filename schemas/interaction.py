from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CommentBase(BaseModel):
    text: str = Field(..., max_length=1000)

class CommentCreate(CommentBase):
    pass

class CommentUpdate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: int
    hobby_id: int
    persona_id: int
    created_at: datetime
    
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
