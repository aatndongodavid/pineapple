from fastapi import APIRouter

router = APIRouter()

@router.get("/posts", summary="Obtenir le fil d'actualités de l'établissement", tags=["Feed & Publications"])
async def get_posts():
    return {"posts": []}

@router.post("/posts", summary="Créer une publication", tags=["Feed & Publications"])
async def create_post():
    return {"message": "Création de publication (à implémenter)"}
