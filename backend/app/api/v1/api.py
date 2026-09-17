from fastapi import APIRouter

from app.api.v1 import health, auth, users, feed, elections, vote, results

api_router = APIRouter()

api_router.include_router(health.router, tags=["Système & Santé"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentification & Identity"])
api_router.include_router(users.router, prefix="/users", tags=["Utilisateurs & Certification"])
api_router.include_router(feed.router, prefix="/feed", tags=["Feed & Publications"])
api_router.include_router(elections.router, prefix="/elections", tags=["Démocratie & Élections"])
api_router.include_router(vote.router, prefix="/vote", tags=["Vote & Audit"])
api_router.include_router(results.router, prefix="/results", tags=["Vote & Audit"])
