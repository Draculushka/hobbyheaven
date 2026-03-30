from fastapi import APIRouter
from . import auth, hobbies, interactions

api_router = APIRouter()
api_router.include_router(auth.router, tags=["api_auth"])
api_router.include_router(hobbies.router, tags=["api_hobbies"])
api_router.include_router(interactions.router, tags=["api_interactions"])
