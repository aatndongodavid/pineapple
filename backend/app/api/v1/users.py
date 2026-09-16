from fastapi import APIRouter

router = APIRouter()

@router.get("/me", summary="Obtenir le profil de l'utilisateur connecté", tags=["Utilisateurs & Certification"])
async def get_me():
    return {"message": "Profil utilisateur (à implémenter)"}

@router.post("/verify", summary="Soumettre une demande de certification académique", tags=["Utilisateurs & Certification"])
async def submit_certification():
    return {"message": "Soumission de certification (à implémenter)"}
