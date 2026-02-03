import json
import uuid
from datetime import datetime, timezone
from typing import Any

import pytest
from flask import Flask
from sqlalchemy.engine.base import Engine
from werkzeug.security import generate_password_hash

from website.models import KEVEntry, User


@pytest.fixture
def client(app: Flask) -> Any:
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def admin_user(session: Engine, request: Any) -> User:
    """Create an admin user for testing"""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        login=f"admin_{unique_id}",
        name="Admin User",
        pwdhash=generate_password_hash("password"),
        email=f"admin_{unique_id}@example.com",
        is_admin=True,
        is_reporter=True,
        is_active=True,
        last_seen=None,
    )
    session.add(user)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]
    return user


@pytest.fixture
def reporter_user(session: Engine, request: Any) -> User:
    """Create a reporter user for testing"""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        login=f"reporter_{unique_id}",
        name="Reporter User",
        pwdhash=generate_password_hash("password"),
        email=f"reporter_{unique_id}@example.com",
        is_reporter=True,
        is_active=True,
        last_seen=None,
    )
    session.add(user)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]
    return user


@pytest.fixture
def regular_user(session: Engine, request: Any) -> User:
    """Create a regular user for testing"""
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        login=f"john_{unique_id}",
        name="John Doe",
        pwdhash=generate_password_hash("password"),
        email=f"john_{unique_id}@doe.example",
        last_seen=None,
    )
    session.add(user)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]
    return user


def test_get_kev_list_empty(client: Any) -> None:
    """Test getting empty KEV list"""
    response = client.get("/api/kev/")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "metadata" in data
    assert "data" in data
    assert data["metadata"]["count"] == 0
    assert len(data["data"]) == 0


def test_create_kev_entry_no_auth(client: Any) -> None:
    """Test creating KEV entry without authentication"""
    kev_data = {
        "vulnerability": {"vulnId": "CVE-2024-1234"},
        "status": {
            "exploited": True,
            "status_reason": "confirmed",
            "status_updated_at": "2024-01-01T00:00:00Z",
        },
    }
    response = client.post(
        "/api/kev/", data=json.dumps(kev_data), content_type="application/json"
    )
    assert response.status_code == 401


def test_create_kev_entry_regular_user(client: Any, regular_user: User) -> None:
    """Test creating KEV entry as regular user (should fail)"""
    kev_data = {
        "vulnerability": {"vulnId": "CVE-2024-1234"},
        "status": {
            "exploited": True,
            "status_reason": "confirmed",
            "status_updated_at": "2024-01-01T00:00:00Z",
        },
    }
    response = client.post(
        "/api/kev/",
        data=json.dumps(kev_data),
        content_type="application/json",
        headers={"X-API-KEY": regular_user.apikey},
    )
    assert response.status_code == 403


def test_create_kev_entry_reporter(client: Any, reporter_user: User, session: Engine) -> None:
    """Test creating KEV entry as reporter"""
    kev_data = {
        "vulnerability": {"vulnId": "CVE-2024-1234"},
        "status": {
            "exploited": True,
            "status_reason": "confirmed",
            "status_updated_at": "2024-01-01T00:00:00Z",
        },
        "characteristics": {"remote_code_execution": True},
        "timestamps": {"first_seen_at": "2024-01-01T00:00:00Z"},
        "scope": {"notes": "Test KEV entry"},
        "references": [{"id": "CVE-2024-1234", "url": "https://example.com"}],
        "evidence": [
            {
                "type": "vendor_report",
                "signal": "successful_exploitation",
                "confidence": 0.8,
                "source": "test-source",
                "details": {"description": "Test evidence"},
            }
        ],
    }
    response = client.post(
        "/api/kev/",
        data=json.dumps(kev_data),
        content_type="application/json",
        headers={"X-API-KEY": reporter_user.apikey},
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert "uuid" in data
    assert data["vulnerability"]["vulnId"] == "CVE-2024-1234"
    assert data["status"]["exploited"] is True
    assert data["status"]["status_reason"] == "confirmed"
    assert len(data["evidence"]) == 1


def test_create_kev_entry_invalid_data(client: Any, reporter_user: User) -> None:
    """Test creating KEV entry with invalid data"""
    kev_data = {
        "vulnerability": {"vulnId": "CVE-2024-1234"},
        # Missing required status field
    }
    response = client.post(
        "/api/kev/",
        data=json.dumps(kev_data),
        content_type="application/json",
        headers={"X-API-KEY": reporter_user.apikey},
    )
    assert response.status_code == 400


def test_get_kev_entry(client: Any, reporter_user: User, session: Engine) -> None:
    """Test getting a single KEV entry"""
    # Create a KEV entry
    kev_entry = KEVEntry(
        vuln_id="CVE-2024-5678",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    session.add(kev_entry)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Get the KEV entry
    response = client.get(f"/api/kev/{kev_entry.uuid}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["uuid"] == str(kev_entry.uuid)
    assert data["vulnerability"]["vulnId"] == "CVE-2024-5678"


def test_get_kev_entry_not_found(client: Any) -> None:
    """Test getting a non-existent KEV entry"""
    fake_uuid = str(uuid.uuid4())
    response = client.get(f"/api/kev/{fake_uuid}")
    assert response.status_code == 404


def test_update_kev_entry_author(client: Any, reporter_user: User, session: Engine) -> None:
    """Test updating KEV entry as the author"""
    # Create a KEV entry
    kev_entry = KEVEntry(
        vuln_id="CVE-2024-9999",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    session.add(kev_entry)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Update the KEV entry
    update_data = {
        "vulnerability": {"vulnId": "CVE-2024-9999"},
        "status": {
            "exploited": False,
            "status_reason": "disputed",
            "status_updated_at": "2024-01-02T00:00:00Z",
        },
    }
    response = client.put(
        f"/api/kev/{kev_entry.uuid}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers={"X-API-KEY": reporter_user.apikey},
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"]["exploited"] is False
    assert data["status"]["status_reason"] == "disputed"


def test_update_kev_entry_not_author(
    client: Any, reporter_user: User, admin_user: User, session: Engine
) -> None:
    """Test updating KEV entry as non-author (should fail)"""
    # Create a KEV entry with reporter_user
    kev_entry = KEVEntry(
        vuln_id="CVE-2024-8888",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    session.add(kev_entry)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Create another reporter user
    other_user = User(
        login="other_reporter",
        name="Other Reporter",
        pwdhash=generate_password_hash("password"),
        email="other@example.com",
        is_reporter=True,
        is_active=True,
        last_seen=None,
    )
    session.add(other_user)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Try to update as other user
    update_data = {
        "vulnerability": {"vulnId": "CVE-2024-8888"},
        "status": {
            "exploited": False,
            "status_reason": "disputed",
            "status_updated_at": "2024-01-02T00:00:00Z",
        },
    }
    response = client.put(
        f"/api/kev/{kev_entry.uuid}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers={"X-API-KEY": other_user.apikey},
    )
    assert response.status_code == 403


def test_update_kev_entry_admin(client: Any, reporter_user: User, admin_user: User, session: Engine) -> None:
    """Test updating KEV entry as admin (should succeed)"""
    # Create a KEV entry with reporter_user
    kev_entry = KEVEntry(
        vuln_id="CVE-2024-7777",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    session.add(kev_entry)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Update as admin
    update_data = {
        "vulnerability": {"vulnId": "CVE-2024-7777"},
        "status": {
            "exploited": False,
            "status_reason": "disputed",
            "status_updated_at": "2024-01-02T00:00:00Z",
        },
    }
    response = client.put(
        f"/api/kev/{kev_entry.uuid}",
        data=json.dumps(update_data),
        content_type="application/json",
        headers={"X-API-KEY": admin_user.apikey},
    )
    assert response.status_code == 200


def test_delete_kev_entry_non_admin(client: Any, reporter_user: User, session: Engine) -> None:
    """Test deleting KEV entry as non-admin (should fail)"""
    # Create a KEV entry
    kev_entry = KEVEntry(
        vuln_id="CVE-2024-6666",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    session.add(kev_entry)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Try to delete as non-admin
    response = client.delete(
        f"/api/kev/{kev_entry.uuid}",
        headers={"X-API-KEY": reporter_user.apikey},
    )
    assert response.status_code == 403


def test_delete_kev_entry_admin(client: Any, admin_user: User, session: Engine) -> None:
    """Test deleting KEV entry as admin"""
    # Create a KEV entry
    kev_entry = KEVEntry(
        vuln_id="CVE-2024-5555",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=admin_user.id,
    )
    session.add(kev_entry)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    kev_uuid = str(kev_entry.uuid)

    # Delete as admin
    response = client.delete(
        f"/api/kev/{kev_uuid}",
        headers={"X-API-KEY": admin_user.apikey},
    )
    assert response.status_code == 200

    # Verify it's deleted
    response = client.get(f"/api/kev/{kev_uuid}")
    assert response.status_code == 404


def test_list_kev_entries_with_filters(client: Any, reporter_user: User, session: Engine) -> None:
    """Test listing KEV entries with filters"""
    # Create multiple KEV entries
    kev1 = KEVEntry(
        vuln_id="CVE-2024-1111",
        exploited=True,
        status_reason="confirmed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    kev2 = KEVEntry(
        vuln_id="CVE-2024-2222",
        exploited=False,
        status_reason="disputed",
        status_updated_at=datetime.now(timezone.utc),
        vulnerability_lookup_origin=uuid.uuid4(),
        author_id=reporter_user.id,
    )
    session.add(kev1)  # type: ignore[attr-defined]
    session.add(kev2)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Filter by exploited status
    response = client.get("/api/kev/?exploited=true")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["metadata"]["count"] >= 1

    # Filter by status_reason
    response = client.get("/api/kev/?status_reason=disputed")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["metadata"]["count"] >= 1

    # Filter by author
    response = client.get(f"/api/kev/?author={reporter_user.login}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["metadata"]["count"] >= 2


def test_list_kev_entries_pagination(client: Any, reporter_user: User, session: Engine) -> None:
    """Test pagination of KEV entries"""
    # Create multiple KEV entries
    for i in range(5):
        kev = KEVEntry(
            vuln_id=f"CVE-2024-{i:04d}",
            exploited=True,
            status_reason="confirmed",
            status_updated_at=datetime.now(timezone.utc),
            vulnerability_lookup_origin=uuid.uuid4(),
            author_id=reporter_user.id,
        )
        session.add(kev)  # type: ignore[attr-defined]
    session.commit()  # type: ignore[attr-defined]

    # Get first page
    response = client.get("/api/kev/?page=1&per_page=2")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["metadata"]["page"] == 1
    assert data["metadata"]["per_page"] == 2
    assert len(data["data"]) <= 2

    # Get second page
    response = client.get("/api/kev/?page=2&per_page=2")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["metadata"]["page"] == 2
