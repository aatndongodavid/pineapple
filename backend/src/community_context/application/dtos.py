from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from community_context.domain.value_objects import (
    AudienceScope,
    OrganizationType,
    PostType,
    RoomStatus,
)


class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PostCreateDTO(BaseDTO):
    content: str
    post_type: PostType
    media_urls: List[str] = []
    organization_id: Optional[UUID] = None
    scope: AudienceScope = AudienceScope.LOCAL


class PostResponseDTO(BaseDTO):
    id: UUID
    tenant_id: UUID
    author_id: UUID
    organization_id: Optional[UUID]
    content: str
    post_type: PostType
    media_urls: List[str]
    scope: AudienceScope
    is_sponsored: bool
    views_count: int
    created_at: datetime


class OrganizationCreateDTO(BaseDTO):
    name: str
    description: str
    type: OrganizationType
    logo_url: Optional[str] = None


class RoomDeclareDTO(BaseDTO):
    room_id: UUID
    status: RoomStatus
    validity_minutes: int = 60