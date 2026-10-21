from __future__ import annotations

import shutil
from pathlib import Path

from conftest import run_git
from fastapi.testclient import TestClient

from notebook_classifier.app import create_app

FIXTURES = Path(__file__).parent / "fixtures"
BASE_URL = "http://127.0.0.1:8765"
ORIGIN = {"Origin": BASE_URL}


def authenticated_client(app) -> TestClient:
    client = TestClient(app, base_url=BASE_URL)
    response = client.get(
        "/session", params={"token": app.state.session_token}, follow_redirects=False
    )
    assert response.status_code == 303
    return client


def test_session_cookie_and_security_headers(
    course_repository: Path, tmp_path: Path
) -> None:
    app = create_app(course_repository, draft_root=tmp_path / "drafts")
    client = TestClient(app, base_url=BASE_URL)

    assert client.get("/").status_code == 403
    client = authenticated_client(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "script-src 'none'" in response.headers["content-security-policy"]
    assert "Repository review" in response.text


def test_non_loopback_host_and_oversized_form_are_rejected(
    course_repository: Path, tmp_path: Path
) -> None:
    app = create_app(course_repository, draft_root=tmp_path / "drafts")
    client = authenticated_client(app)

    assert client.get("/", headers={"Host": "example.invalid"}).status_code == 400
    response = client.post(
        "/notebook",
        content=b"x" * (128 * 1024 + 1),
        headers={
            "Origin": BASE_URL,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert response.status_code == 413


def test_detail_route_cannot_browse_arbitrary_files(
    course_repository: Path, tmp_path: Path
) -> None:
    app = create_app(course_repository, draft_root=tmp_path / "drafts")
    client = authenticated_client(app)

    response = client.get("/notebook", params={"path": "../../etc/passwd"})

    assert response.status_code == 400
    assert "unknown tracked notebook" in response.text


def test_cross_origin_and_bad_csrf_writes_are_rejected(
    course_repository: Path, tmp_path: Path
) -> None:
    app = create_app(course_repository, draft_root=tmp_path / "drafts")
    client = authenticated_client(app)
    data = {
        "csrf": app.state.csrf_token,
        "path": "notebooks/tutorial.ipynb",
        "reviewer": "Maintainer",
    }

    assert client.post("/notebook", data=data).status_code == 403
    data["csrf"] = "wrong"
    assert client.post("/notebook", data=data, headers=ORIGIN).status_code == 403


def test_detail_preview_is_safe_and_decision_stays_in_draft(
    course_repository: Path, tmp_path: Path
) -> None:
    hostile = course_repository / "notebooks" / "hostile.ipynb"
    shutil.copyfile(FIXTURES / "hostile.ipynb", hostile)
    run_git(course_repository, "add", str(hostile.relative_to(course_repository)))
    before = hostile.read_bytes()
    app = create_app(course_repository, draft_root=tmp_path / "drafts")
    client = authenticated_client(app)

    response = client.get("/notebook", params={"path": "notebooks/hostile.ipynb"})

    assert response.status_code == 200
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
    assert "onerror=alert" not in response.text
    assert "Omitted display_data output" in response.text

    response = client.post(
        "/notebook",
        data={
            "csrf": app.state.csrf_token,
            "path": "notebooks/hostile.ipynb",
            "reviewer": "Maintainer",
            "role": "tutorial",
            "delivery_scope": "core",
            "output_policy": "declared_errors",
            "validation_tier": "manual",
            "environment": "default",
            "lifecycle": "active",
            "runtime": "short",
            "constraints_mode": "override",
            "constraints": ["network", "manual_interaction"],
            "rationale": "Hostile fixture for static review.",
        },
        headers=ORIGIN,
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert hostile.read_bytes() == before
    assert not (course_repository / "validation" / "manifest.toml").exists()


def test_rule_preview_lists_affected_notebooks(
    course_repository: Path, tmp_path: Path
) -> None:
    app = create_app(course_repository, draft_root=tmp_path / "drafts")
    client = authenticated_client(app)

    response = client.post(
        "/rules/preview",
        data={
            "csrf": app.state.csrf_token,
            "rule_id": "tutorials",
            "include": "notebooks/*.ipynb",
            "property_name": "role",
            "value": "tutorial",
        },
        headers=ORIGIN,
    )

    assert response.status_code == 200
    assert "notebooks/tutorial.ipynb" in response.text
    assert "1 tracked notebook(s)" in response.text
