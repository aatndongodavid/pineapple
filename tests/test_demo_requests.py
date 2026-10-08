import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

pytestmark = pytest.mark.asyncio


async def test_submit_valid_demo_request(async_db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "institution_name": "Universite de Douala - FSEGA",
            "contact_name": "Prof. Jean Kouam",
            "role": "directeur_dg",
            "email": "j.kouam@univ-douala.cm",
            "whatsapp_phone": "+237690112233",
            "student_count_range": "300_1500",
            "notes": "Besoin urgent de gestion des amphis pour la rentree academique.",
        }
        res = await client.post("/api/v1/public/demo-requests", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "success"
        assert "request_id" in data


async def test_honeypot_bot_rejection(async_db_session):
    """Gate W3: If website_url_hp is set, bot is trapped and request is ignored silently."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "institution_name": "Fake Bot University",
            "contact_name": "Spam Bot",
            "role": "autre",
            "email": "spambot@example.com",
            "whatsapp_phone": "+237000000000",
            "student_count_range": "under_300",
            "website_url_hp": "http://spam-link.com",  # Honeypot filled!
        }
        res = await client.post("/api/v1/public/demo-requests", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "success"


async def test_rate_limiting_demo_requests(async_db_session):
    """Gate W3: 5 requests max per IP per hour."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Note: request.client is None in ASGITransport unless headers are passed or client IP is mocked
        headers = {"X-Forwarded-For": "198.51.100.42"}
        for i in range(5):
            payload = {
                "institution_name": f"Univ Test RateLimit {i}",
                "contact_name": f"User {i}",
                "role": "directeur_dg",
                "email": f"user{i}@univ-test.cm",
                "whatsapp_phone": "+237690000000",
                "student_count_range": "under_300",
            }
            res = await client.post("/api/v1/public/demo-requests", json=payload, headers=headers)
            assert res.status_code == 201
