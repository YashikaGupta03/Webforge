from __future__ import annotations

from typing import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.core.config import settings
from app.core.security import hash_password
from app.api.routes.auth import DEMO_ROLES
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.department import Department, Hostel
from app.models.user import User
from app import models  # noqa: F401
from app.api.routes.auth import DEMO_ROLES


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setattr(settings, "secret_key", "test-only-secret-key-with-at-least-32-bytes")
    monkeypatch.setattr(settings, "app_environment", "development")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = factory()
    department = Department(name="Electrical", sla_hours=4)
    hostel = Hostel(name="Test Hostel", block="Test Block")
    session.add_all([department, hostel])
    session.flush()
    session.add_all([
        User(
            id=str(uuid4()),
            scholar_no="ADMIN-1",
            email="admin@example.test",
            name="Test Admin",
            role="Super Admin",
            password_hash=hash_password("Test-Admin-Password"),
        ),
        User(
            id=str(uuid4()),
            scholar_no="STUDENT-1",
            email="student@example.test",
            name="Test Student",
            role="Student",
            password_hash=hash_password("Test-Student-Password"),
            hostel_id=hostel.id,
        ),
        User(
            id=str(uuid4()),
            scholar_no="STAFF-1",
            email="staff@example.test",
            name="Test Electrician",
            role="Department Staff",
            password_hash=hash_password("Test-Staff-Password"),
            department_id=department.id,
        ),
        User(
            id=str(uuid4()),
            scholar_no="SHORT-PASSWORD-1",
            email="short-password@example.test",
            name="Short Password Test",
            role="Student",
            password_hash=hash_password("1234"),
            hostel_id=hostel.id,
        ),
    ])
    session.commit()
    session.close()

    def override_get_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, client=("127.0.0.1", 12345)) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def access_headers(client: TestClient, scholar_no: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"scholar_no": scholar_no, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_requires_scholar_number_and_valid_password(client: TestClient) -> None:
    accepted = client.post(
        "/api/auth/login",
        json={"scholar_no": "STUDENT-1", "password": "Test-Student-Password"},
    )
    assert accepted.status_code == 200

    short_valid_password = client.post(
        "/api/auth/login",
        json={"scholar_no": "SHORT-PASSWORD-1", "password": "1234"},
    )
    assert short_valid_password.status_code == 200

    incorrect_short_password = client.post(
        "/api/auth/login",
        json={"scholar_no": "STUDENT-1", "password": "1234"},
    )
    assert incorrect_short_password.status_code == 401

    empty_password = client.post(
        "/api/auth/login",
        json={"scholar_no": "STUDENT-1", "password": ""},
    )
    assert empty_password.status_code == 422

    email_login = client.post(
        "/api/auth/login",
        json={"scholar_no": "student@example.test", "password": "Test-Student-Password"},
    )
    assert email_login.status_code == 401


def test_student_signup_saves_account_that_can_sign_in(client: TestClient) -> None:
    signup = client.post(
        "/api/auth/signup",
        json={
            "email": "New.Student@example.com",
            "scholar_no": " NEW-STUDENT-1 ",
            "name": " New Student ",
            "password": "Long-Student-Password",
        },
    )
    assert signup.status_code == 201
    assert signup.json()["email"] == "new.student@example.com"
    assert signup.json()["scholar_no"] == "NEW-STUDENT-1"
    assert signup.json()["name"] == "New Student"
    assert signup.json()["role"] == "Student"
    assert "password_hash" not in signup.json()

    login = client.post(
        "/api/auth/login",
        json={"scholar_no": "NEW-STUDENT-1", "password": "Long-Student-Password"},
    )
    assert login.status_code == 200
    assert login.json()["role"] == "Student"


def test_student_signup_rejects_duplicate_accounts_and_short_passwords(client: TestClient) -> None:
    account = {
        "email": "new.student@example.com",
        "scholar_no": "NEW-STUDENT-1",
        "name": "New Student",
        "password": "Long-Student-Password",
    }
    assert client.post("/api/auth/signup", json=account).status_code == 201
    assert client.post("/api/auth/signup", json=account).status_code == 409

    account["email"] = "another.student@example.com"
    account["scholar_no"] = "NEW-STUDENT-2"
    account["password"] = "short"
    assert client.post("/api/auth/signup", json=account).status_code == 422


@pytest.mark.parametrize("role", DEMO_ROLES)
def test_demo_login_issues_selected_local_role(client: TestClient, role: str) -> None:
    response = client.post("/api/auth/demo-login", json={"role": role})
    assert response.status_code == 200
    assert response.json()["role"] == role
    assert response.json()["access_token"]


def test_demo_login_is_disabled_outside_local_development(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "app_environment", "production")
    response = client.post("/api/auth/demo-login", json={"role": "Super Admin"})
    assert response.status_code == 404

    monkeypatch.setattr(settings, "app_environment", "development")
    remote_client = TestClient(app, client=("192.0.2.10", 12345))
    response = remote_client.post("/api/auth/demo-login", json={"role": "Super Admin"})
    assert response.status_code == 404


def test_issue_workflow_and_role_scoping(client: TestClient) -> None:
    student_headers = access_headers(client, "STUDENT-1", "Test-Student-Password")
    admin_headers = access_headers(client, "ADMIN-1", "Test-Admin-Password")
    staff_headers = access_headers(client, "STAFF-1", "Test-Staff-Password")

    created = client.post(
        "/api/issues",
        headers=student_headers,
        json={
            "title": "Sparking power wire",
            "description": "A live wire is sparking near the hostel entrance.",
            "category": "Electrical",
            "location": "Test Hostel entrance",
        },
    )
    assert created.status_code == 201
    issue = created.json()
    assert issue["status"] == "Submitted"
    assert issue["priority"] == "Critical"

    student_issues = client.get("/api/issues", headers=student_headers)
    assert [item["id"] for item in student_issues.json()] == [issue["id"]]

    chat = client.post(
        "/api/issues/chat",
        headers=student_headers,
        json={"message": "Water is leaking from a pipe", "draft": {}},
    )
    assert chat.status_code == 200
    assert chat.json()["draft"]["category"] == "Plumbing and Water"

    assignment = client.patch(
        f"/api/issues/{issue['id']}/assignment",
        headers=admin_headers,
        json={"department": "Electrical", "staff_name": "Test Electrician"},
    )
    assert assignment.status_code == 200
    assert assignment.json()["status"] == "Assigned"
    assert client.get("/api/issues", headers=staff_headers).json()[0]["id"] == issue["id"]
    assert client.get("/api/audit", headers=student_headers).status_code == 403

    notices = client.get("/api/notifications", headers=student_headers)
    assert notices.status_code == 200
    assert notices.json()


def test_duplicate_response_uses_public_issue_token(client: TestClient) -> None:
    student_headers = access_headers(client, "STUDENT-1", "Test-Student-Password")
    admin_headers = access_headers(client, "ADMIN-1", "Test-Admin-Password")
    first = client.post(
        "/api/issues",
        headers=student_headers,
        json={
            "title": "Broken hallway light",
            "description": "The hallway light is broken.",
            "category": "Electrical",
            "location": "Test Hostel hallway",
        },
    )
    second = client.post(
        "/api/issues",
        headers=student_headers,
        json={
            "title": "Light not working",
            "description": "A light is not working in the hallway.",
            "category": "Electrical",
            "location": "Test Hostel hallway",
        },
    )
    assert first.status_code == second.status_code == 201

    linked = client.post(
        f"/api/issues/{second.json()['id']}/duplicates",
        headers=admin_headers,
        json={"duplicate_of": first.json()["id"]},
    )
    assert linked.status_code == 200
    assert linked.json()["duplicateOf"] == first.json()["id"]
