from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="Lister les élections de l'établissement", tags=["Démocratie & Élections"])
async def list_elections():
    return {"elections": []}
