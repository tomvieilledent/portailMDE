from fastapi import APIRouter

from app.api.v1 import auth, chat, companies, directory, events, users, ws

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(companies.router)
api_router.include_router(directory.router)
api_router.include_router(chat.router)
api_router.include_router(events.router)
api_router.include_router(ws.router)
