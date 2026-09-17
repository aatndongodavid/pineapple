from fastapi import APIRouter

router = APIRouter()

@router.post("/login", summary="Connexion utilisateur (JWT)", tags=["Authentification & Identity"])
async def login():
    return {"message": "Endpoint d'authentification (à implémenter)"}

@router.post("/register", summary="Inscription utilisateur", tags=["Authentification & Identity"])
async def register():
    return {"message": "Endpoint d'inscription (à implémenter)"}
