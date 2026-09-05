# backend/src/scripts/seed_data.py

import asyncio
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from passlib.context import CryptContext
from sqlalchemy import select

from identity_context.infrastructure.persistence.models import UserModel
from democracy_context.infrastructure.persistence.models import ElectionModel, MovementModel
from community_context.infrastructure.persistence.models import RoomModel
from shared_kernel.infrastructure.database import AsyncSessionLocal, Base
from shared_kernel.domain.value_objects import Money
from identity_context.domain.value_objects import (
    AccountStatus,
    AcademicStatus,
    VerificationStatus,
)
from democracy_context.domain.entities import ElectionStatus, MovementStatus
from community_context.domain.value_objects import RoomStatus

# Configuration du hachage des mots de passe (identique à l'application)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# UUID fixes pour la démonstration (facilite l'idempotence)
TENANT_ENSPD = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
STUDENT1_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
STUDENT2_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
ELECTION_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
MOVEMENT1_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
MOVEMENT2_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
ROOM1_ID = uuid.UUID("aaaaaaaa-1111-1111-1111-111111111111")
ROOM2_ID = uuid.UUID("bbbbbbbb-2222-2222-2222-222222222222")
ROOM3_ID = uuid.UUID("cccccccc-3333-3333-3333-333333333333")


async def seed_data() -> None:
    """Peuple la base de données avec le jeu de données de démonstration."""
    async with AsyncSessionLocal() as session:
        # Vérifier si le seed a déjà été exécuté (en testant un utilisateur)
        existing_admin = await session.execute(
            select(UserModel).where(UserModel.email == "admin@enspd.cm")
        )
        if existing_admin.scalar_one_or_none():
            print("Seed déjà exécuté, aucune insertion.")
            return

        # ---------- Utilisateurs ----------
        # Super Admin Établissement (enseignant vérifié, rôle admin à configurer séparément)
        admin = UserModel(
            id=ADMIN_ID,
            tenant_id=TENANT_ENSPD,
            email="admin@enspd.cm",
            hashed_password=pwd_context.hash("Admin123!"),
            first_name="Super",
            last_name="Admin",
            matricule="ADMIN001",
            faculty="Administration",
            filiere="N/A",
            academic_year="2026-2027",
            account_status=AccountStatus.ACTIVE,
            verification_status=VerificationStatus.VERIFIED,
            academic_status=AcademicStatus.TEACHER,  # Rôle admin à ajouter via RBAC
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Étudiant 1 certifié
        student1 = UserModel(
            id=STUDENT1_ID,
            tenant_id=TENANT_ENSPD,
            email="etudiant1@enspd.cm",
            hashed_password=pwd_context.hash("Etudiant123!"),
            first_name="Alice",
            last_name="Ndongo",
            matricule="ENSPD2026001",
            faculty="Génie Logiciel",
            filiere="Informatique",
            academic_year="2026-2027",
            account_status=AccountStatus.ACTIVE,
            verification_status=VerificationStatus.VERIFIED,
            academic_status=AcademicStatus.STUDENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Étudiant 2 certifié
        student2 = UserModel(
            id=STUDENT2_ID,
            tenant_id=TENANT_ENSPD,
            email="etudiant2@enspd.cm",
            hashed_password=pwd_context.hash("Etudiant123!"),
            first_name="Bob",
            last_name="Kamga",
            matricule="ENSPD2026002",
            faculty="Génie Électrique",
            filiere="Électrotechnique",
            academic_year="2026-2027",
            account_status=AccountStatus.ACTIVE,
            verification_status=VerificationStatus.VERIFIED,
            academic_status=AcademicStatus.STUDENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add_all([admin, student1, student2])

        # ---------- Élection de démonstration ----------
        election = ElectionModel(
            id=ELECTION_ID,
            tenant_id=TENANT_ENSPD,
            title="Élection BDE ENSPD 2027",
            election_type="BDE",
            status=ElectionStatus.CAMPAIGN,
            eligibility_rules={
                "level": "L3",
                "filiere": ["Génie Logiciel", "Génie Électrique"],
                "certified": True,
            },
            config={},
            voting_start_at=datetime.utcnow() + timedelta(days=10),
            voting_end_at=datetime.utcnow() + timedelta(days=11),
            created_at=datetime.utcnow(),
        )
        session.add(election)

        # ---------- Mouvements concurrents ----------
        movement1 = MovementModel(
            id=MOVEMENT1_ID,
            election_id=ELECTION_ID,
            tenant_id=TENANT_ENSPD,
            name="Mouvement Bleu",
            slogan="Transparence et Progrès",
            program_text="Programme du Mouvement Bleu : amélioration des infrastructures, plus de transparence.",
            status=MovementStatus.APPROVED,
        )
        movement2 = MovementModel(
            id=MOVEMENT2_ID,
            election_id=ELECTION_ID,
            tenant_id=TENANT_ENSPD,
            name="Alliance Innovation",
            slogan="Innover pour l'avenir",
            program_text="Programme de l'Alliance Innovation : digitalisation des services, soutien aux projets étudiants.",
            status=MovementStatus.APPROVED,
        )
        session.add_all([movement1, movement2])

        # ---------- Salles de classe ----------
        room1 = RoomModel(
            id=ROOM1_ID,
            tenant_id=TENANT_ENSPD,
            name="Salle A101",
            building="Bâtiment A",
            status=RoomStatus.FREE,
            declared_by_user_id=ADMIN_ID,
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        room2 = RoomModel(
            id=ROOM2_ID,
            tenant_id=TENANT_ENSPD,
            name="Salle B202",
            building="Bâtiment B",
            status=RoomStatus.OCCUPIED,
            declared_by_user_id=ADMIN_ID,
            expires_at=None,
        )
        room3 = RoomModel(
            id=ROOM3_ID,
            tenant_id=TENANT_ENSPD,
            name="Amphi 500",
            building="Amphithéâtre",
            status=RoomStatus.TO_CONFIRM,
            declared_by_user_id=ADMIN_ID,
            expires_at=None,
        )
        session.add_all([room1, room2, room3])

        # ---------- Commit final ----------
        try:
            await session.commit()
            print("Seed exécuté avec succès.")
        except Exception as e:
            await session.rollback()
            print(f"Erreur lors du seed : {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())