import asyncio

from shared_kernel.infrastructure.database import Base, engine

import academy_context.infrastructure.persistence.models
import campus_life_context.infrastructure.persistence.models
import community_context.infrastructure.persistence.models
import democracy_context.infrastructure.persistence.models
import identity_context.infrastructure.persistence.models
import monetization_context.infrastructure.persistence.models
import opportunities_context.infrastructure.persistence.models
import trust_safety_context.infrastructure.persistence.models


async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(create_tables())
