import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

from shared_kernel.infrastructure.auth import get_current_user
from shared_kernel.infrastructure.tenant_middleware import get_current_tenant_id

router = APIRouter(prefix="/search", tags=["Global Unified Search"])


class SearchResultItemDTO(BaseModel):
    id: str
    type: str = Field(..., description="Type de contenu: 'post', 'organization', 'academy_document', 'opportunity'")
    title: str
    description: Optional[str] = None
    url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GlobalSearchResponseDTO(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItemDTO]


@router.get("", response_model=GlobalSearchResponseDTO)
async def global_unified_search(
    q: str = Query(..., min_length=2, description="Terme ou mots-clés de recherche transversale"),
    content_type: Optional[str] = Query(None, description="Filtre optionnel par type: post, organization, academy, opportunity"),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    current_user: dict = Depends(get_current_user),
):
    """
    Moteur de recherche unifié (Variété Z3) interrogeant les publications du fil,
    les clubs/associations, les ressources de l'Academy et les opportunités de carrière.
    """
    clean_query = q.strip().lower()
    results: List[SearchResultItemDTO] = []

    # Mock/simulé d'indexation unifiée full-text SQL/Meilisearch
    sample_data = [
        {
            "id": "post-101",
            "type": "post",
            "title": "Conférence sur l'IA et la Blockchain au Campus",
            "description": "Rejoignez-nous ce vendredi dans l'amphi principal pour discuter d'IA.",
            "url": "/community/feed",
            "metadata": {"author": "Club Tech", "likes": 42}
        },
        {
            "id": "org-202",
            "type": "organization",
            "title": "Club Robotics & AI",
            "description": "L'association des passionnés de robotique de l'université.",
            "url": "/community/organizations",
            "metadata": {"members_count": 128}
        },
        {
            "id": "doc-303",
            "type": "academy_document",
            "title": "Annales d'Algorithmique & Structures de Données L2",
            "description": "Sujets d'examen corrigés de 2020 à 2025.",
            "url": "/academy/library",
            "metadata": {"file_type": "PDF", "course": "INF201"}
        },
        {
            "id": "opp-404",
            "type": "opportunity",
            "title": "Offre de Stage Développeur Python / Data",
            "description": "Stage de 6 mois rémunéré en ingénierie logicielle.",
            "url": "/opportunities",
            "metadata": {"company": "TechCameroon", "location": "Douala"}
        },
    ]

    for item in sample_data:
        # Filtrage par type si spécifié
        if content_type and item["type"] != content_type:
            continue

        # Matching de recherche sur titre ou description
        if clean_query in item["title"].lower() or clean_query in item["description"].lower():
            results.append(SearchResultItemDTO(**item))

    return GlobalSearchResponseDTO(
        query=q,
        total_results=len(results),
        results=results,
    )
