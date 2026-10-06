import asyncio
from datetime import datetime, timedelta, timezone
import uuid

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from community_context.infrastructure.persistence.models import RoomModel
from identity_context.infrastructure.persistence.models import (
    ClassDelegateModel,
    ClassGroupModel,
    MembershipModel,
    RosterEntryModel,
    TenantModel,
    TenantSubscriptionModel,
    UserModel,
)
from monetization_context.infrastructure.persistence.models import (
    AdCampaignModel,
    AdCreativeModel,
)
from shared_kernel.infrastructure.database import AsyncSessionLocal, engine, Base
from shared_kernel.infrastructure.encryption import encrypt_field, normalize_matricule, normalize_text

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("[SEED] Demarrage du seed de developpement Pineapple OS...")
        now = datetime.now(timezone.utc)

        # 1. Super Admin Plateforme
        sa_email = "superadmin@pineapple.cm"
        sa_stmt = select(UserModel).where(UserModel.email == sa_email)
        super_admin = (await db.execute(sa_stmt)).scalars().first()
        if not super_admin:
            super_admin = UserModel(
                id=uuid.uuid4(),
                email=sa_email,
                hashed_password=pwd_context.hash("SuperAdmin2026!"),
                first_name="Super",
                last_name="Admin",
                user_type="PLATFORM_ADMIN",
                account_status="ACTIVE",
            )
            db.add(super_admin)
            print("  [+] Super Admin créé : superadmin@pineapple.cm / SuperAdmin2026!")

        # 2. Établissement ENSPD (Abonnement Actif)
        enspd_stmt = select(TenantModel).where(TenantModel.code == "ENSPD")
        enspd = (await db.execute(enspd_stmt)).scalars().first()
        if not enspd:
            enspd = TenantModel(
                id=uuid.uuid4(),
                name="École Nationale Supérieure Polytechnique de Douala",
                code="ENSPD",
                country="Cameroun",
                enrollment_mode="BOTH",
                auto_approve_claims=True,
                current_academic_year="2026-2027",
                is_active=True,
            )
            db.add(enspd)
            db.add(
                TenantSubscriptionModel(
                    id=uuid.uuid4(),
                    tenant_id=enspd.id,
                    plan="PREMIUM",
                    status="ACTIVE",
                    seats_limit=2500,
                    starts_at=now,
                    ends_at=now + timedelta(days=365),
                )
            )
            print("  [+] Établissement ENSPD créé (Abonnement Actif)")

        # 3. Établissement DEMO-EXPIRED (Abonnement Expiré)
        demo_stmt = select(TenantModel).where(TenantModel.code == "DEMO-EXPIRED")
        demo = (await db.execute(demo_stmt)).scalars().first()
        if not demo:
            demo = TenantModel(
                id=uuid.uuid4(),
                name="Institut Démo Expiré",
                code="DEMO-EXPIRED",
                country="Cameroun",
                enrollment_mode="BOTH",
                auto_approve_claims=False,
                current_academic_year="2026-2027",
                is_active=True,
            )
            db.add(demo)
            db.add(
                TenantSubscriptionModel(
                    id=uuid.uuid4(),
                    tenant_id=demo.id,
                    plan="STANDARD",
                    status="EXPIRED",
                    seats_limit=100,
                    starts_at=now - timedelta(days=400),
                    ends_at=now - timedelta(days=10),
                )
            )
            print("  [+] Établissement DEMO-EXPIRED créé (Abonnement Expiré)")

        await db.flush()

        # 4. Classes (ClassGroups) dans ENSPD
        cg_git3 = (await db.execute(select(ClassGroupModel).where(ClassGroupModel.tenant_id == enspd.id, ClassGroupModel.code == "GIT-3"))).scalars().first()
        if not cg_git3:
            cg_git3 = ClassGroupModel(
                id=uuid.uuid4(),
                tenant_id=enspd.id,
                name="Génie Informatique & Télécommunications 3",
                code="GIT-3",
                faculty="Génie Informatique",
                filiere="GIT",
                level="Licence 3",
                academic_year="2026-2027",
                capacity=120,
            )
            db.add(cg_git3)

        cg_gme4 = (await db.execute(select(ClassGroupModel).where(ClassGroupModel.tenant_id == enspd.id, ClassGroupModel.code == "GME-4"))).scalars().first()
        if not cg_gme4:
            cg_gme4 = ClassGroupModel(
                id=uuid.uuid4(),
                tenant_id=enspd.id,
                name="Génie Mécanique 4",
                code="GME-4",
                faculty="Génie Mécanique",
                filiere="GME",
                level="Master 1",
                academic_year="2026-2027",
                capacity=90,
            )
            db.add(cg_gme4)

        await db.flush()

        # 5. Salles Physiques dans ENSPD
        rooms_data = [
            ("Amphi 500", "Bâtiment Principal", 500),
            ("Amphi 200", "Bâtiment Annexe", 200),
            ("Salle TD 12", "Bâtiment B", 60),
            ("Salle TD 14", "Bâtiment B", 60),
            ("Labo TP Info", "Bâtiment Informatique", 40),
            ("Bibliothèque Central", "Bâtiment C", 150),
        ]
        for name, building, cap in rooms_data:
            r_ex = (await db.execute(select(RoomModel).where(RoomModel.tenant_id == enspd.id, RoomModel.name == name))).scalars().first()
            if not r_ex:
                db.add(RoomModel(id=uuid.uuid4(), tenant_id=enspd.id, name=name, building=building, capacity=cap, status="FREE"))

        # 6. Admin d'établissement ENSPD
        admin_email = "admin@enspd.cm"
        admin_u = (await db.execute(select(UserModel).where(UserModel.email == admin_email))).scalars().first()
        if not admin_u:
            admin_u = UserModel(
                id=uuid.uuid4(),
                email=admin_email,
                hashed_password=pwd_context.hash("AdminENSPD2026!"),
                first_name="Jeanne",
                last_name="Eba",
                user_type="STANDARD",
                account_status="ACTIVE",
            )
            db.add(admin_u)
            await db.flush()
            db.add(MembershipModel(id=uuid.uuid4(), tenant_id=enspd.id, user_id=admin_u.id, role="TENANT_ADMIN", status="ACTIVE", joined_via="ADMIN", academic_year="2026-2027"))
            print("  [+] Admin Établissement créé : admin@enspd.cm / AdminENSPD2026!")

        # 7. Étudiant Standard ENSPD (GIT-3)
        stud_email = "student@enspd.cm"
        stud_u = (await db.execute(select(UserModel).where(UserModel.email == stud_email))).scalars().first()
        if not stud_u:
            stud_u = UserModel(
                id=uuid.uuid4(),
                email=stud_email,
                hashed_password=pwd_context.hash("Student2026!"),
                first_name="Paul",
                last_name="Atangana",
                user_type="STANDARD",
                account_status="ACTIVE",
            )
            db.add(stud_u)
            await db.flush()

            roster_p = RosterEntryModel(
                id=uuid.uuid4(),
                tenant_id=enspd.id,
                matricule="21U001",
                last_name="ATANGANA",
                first_name="PAUL",
                birth_date=encrypt_field("2003-05-14"),
                birth_place=encrypt_field("YAOUNDE"),
                norm_matricule="21U001",
                norm_first_name="paul",
                norm_last_name="atangana",
                norm_birth_date="2003-05-14",
                norm_birth_place="yaounde",
                class_group_id=cg_git3.id,
                academic_year="2026-2027",
                official_email=stud_email,
                status="CLAIMED",
                claimed_by_user_id=stud_u.id,
                claimed_at=now,
            )
            db.add(roster_p)
            await db.flush()

            db.add(MembershipModel(id=uuid.uuid4(), tenant_id=enspd.id, user_id=stud_u.id, roster_entry_id=roster_p.id, class_group_id=cg_git3.id, role="STUDENT", status="ACTIVE", joined_via="CLAIM", academic_year="2026-2027"))
            print("  [+] Étudiant Standard créé : student@enspd.cm / Student2026!")

        # 8. Délégué Titulaire ENSPD (GIT-3)
        del_email = "delegate@enspd.cm"
        del_u = (await db.execute(select(UserModel).where(UserModel.email == del_email))).scalars().first()
        if not del_u:
            del_u = UserModel(
                id=uuid.uuid4(),
                email=del_email,
                hashed_password=pwd_context.hash("Delegate2026!"),
                first_name="Marc",
                last_name="Nguema",
                user_type="STANDARD",
                account_status="ACTIVE",
            )
            db.add(del_u)
            await db.flush()

            roster_d = RosterEntryModel(
                id=uuid.uuid4(),
                tenant_id=enspd.id,
                matricule="21U002",
                last_name="NGUEMA",
                first_name="MARC",
                birth_date=encrypt_field("2002-11-20"),
                birth_place=encrypt_field("DOUALA"),
                norm_matricule="21U002",
                norm_first_name="marc",
                norm_last_name="nguema",
                norm_birth_date="2002-11-20",
                norm_birth_place="douala",
                class_group_id=cg_git3.id,
                academic_year="2026-2027",
                official_email=del_email,
                status="CLAIMED",
                claimed_by_user_id=del_u.id,
                claimed_at=now,
            )
            db.add(roster_d)
            await db.flush()

            db.add(MembershipModel(id=uuid.uuid4(), tenant_id=enspd.id, user_id=del_u.id, roster_entry_id=roster_d.id, class_group_id=cg_git3.id, role="STUDENT", status="ACTIVE", joined_via="CLAIM", academic_year="2026-2027"))
            db.add(ClassDelegateModel(id=uuid.uuid4(), tenant_id=enspd.id, class_group_id=cg_git3.id, user_id=del_u.id, kind="TITULAIRE", appointed_by=admin_u.id, appointed_at=now))
            print("  [+] Délégué de classe créé : delegate@enspd.cm / Delegate2026!")

        # 9. Visiteur sans appartenance
        vis_email = "visitor@pineapple.cm"
        vis_u = (await db.execute(select(UserModel).where(UserModel.email == vis_email))).scalars().first()
        if not vis_u:
            vis_u = UserModel(
                id=uuid.uuid4(),
                email=vis_email,
                hashed_password=pwd_context.hash("Visitor2026!"),
                first_name="Charles",
                last_name="Mbarga",
                user_type="STANDARD",
                account_status="ACTIVE",
            )
            db.add(vis_u)
            print("  [+] Compte Visiteur créé : visitor@pineapple.cm / Visitor2026!")

        # 10. Données de Registre non réclamées pour tests Mode A (claim)
        roster_unclaimed_data = [
            ("21U010", "EBOUE", "EMMANUEL", "2003-01-10", "DOUALA"),
            ("21U011", "KOUAM", "FRANCK", "2002-08-25", "BAFOUSSAM"),
            ("21U012", "NKEN", "STEPHANIE", "2003-04-12", "YAOUNDE"),
            ("21U013", "BILO'O", "CHRISTIAN", "2002-12-01", "EBOLOWA"),
            ("21U014", "FOPA", "HERMAN", "2003-09-18", "DSCHANG"),
        ]
        for mat, last, first, bdate, bplace in roster_unclaimed_data:
            r_ex = (await db.execute(select(RosterEntryModel).where(RosterEntryModel.tenant_id == enspd.id, RosterEntryModel.matricule == mat))).scalars().first()
            if not r_ex:
                db.add(
                    RosterEntryModel(
                        id=uuid.uuid4(),
                        tenant_id=enspd.id,
                        matricule=mat,
                        last_name=last,
                        first_name=first,
                        birth_date=encrypt_field(bdate),
                        birth_place=encrypt_field(bplace),
                        norm_matricule=normalize_matricule(mat),
                        norm_first_name=normalize_text(first),
                        norm_last_name=normalize_text(last),
                        norm_birth_date=bdate,
                        norm_birth_place=normalize_text(bplace),
                        class_group_id=cg_git3.id,
                        academic_year="2026-2027",
                        status="NOT_CLAIMED",
                    )
                )

        # 11. Publicités pour Visiteurs
        camp_stmt = select(AdCampaignModel).where(AdCampaignModel.title == "Offre Étudiante MTN MoMo")
        camp = (await db.execute(camp_stmt)).scalars().first()
        if not camp:
            camp = AdCampaignModel(
                id=uuid.uuid4(),
                title="Offre Étudiante MTN MoMo",
                advertiser_name="MTN Cameroun",
                status="ACTIVE",
                target_url="https://www.mtn.cm",
            )
            db.add(camp)
            await db.flush()

            db.add(
                AdCreativeModel(
                    id=uuid.uuid4(),
                    campaign_id=camp.id,
                    headline="Forfait Data Étudiant 10 Go à 1000 FCFA",
                    body_text="Profite du haut débit MTN sur ton campus. Active ton pass directement sur MoMo.",
                    image_url="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
                    cta_text="Souscrire sur MoMo",
                    is_active=True,
                )
            )
            db.add(
                AdCreativeModel(
                    id=uuid.uuid4(),
                    campaign_id=camp.id,
                    headline="Stage & Emploi chez Orange Digital Center",
                    body_text="Dépose ton CV pour les programmes d'incubation et d'alternance 2026-2027.",
                    image_url="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800",
                    cta_text="Postuler maintenant",
                    is_active=True,
                )
            )

        await db.commit()
        print("[SEED] Seed termine avec succes !")


if __name__ == "__main__":
    asyncio.run(seed())