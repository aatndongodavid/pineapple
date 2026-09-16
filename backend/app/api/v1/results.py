from fastapi import APIRouter

router = APIRouter()

@router.get("/{election_id}", summary="Consulter les résultats d'une élection", tags=["Vote & Audit"])
async def get_results(election_id: str):
    return {"election_id": election_id, "status": "closed", "results": {}}
