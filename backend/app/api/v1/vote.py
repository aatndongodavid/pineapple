from fastapi import APIRouter

router = APIRouter()

@router.post("/", summary="Soumettre un bulletin de vote sécurisé et anonyme", tags=["Vote & Audit"])
async def cast_vote():
    return {"message": "Vote soumis (à implémenter)"}
