"""
Tests for File Service endpoints (Phase 1: functional + security).

Run with::

    pytest -q

The testcontainers fixtures skip gracefully when Docker is unavailable.
"""

from __future__ import annotations


import pytest

from src.config import settings
from src.main import app
from src.services import quota_service
from src.utils.dependencies import get_current_user_id

# Re-use the canonical test user ids from helpers.
from tests.helpers import (
    USER_ALICE,
    USER_BOB,
    make_jwt,
)
from tests.conftest import switch_user


# ==================== Folder Tests ====================


@pytest.mark.asyncio
async def test_create_folder(async_client):
    response = await async_client.post("/api/folders/", json={"name": "My Documents"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Documents"
    assert "id" in data
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_create_nested_folder(async_client):
    parent_resp = await async_client.post("/api/folders/", json={"name": "Parent"})
    parent_id = parent_resp.json()["id"]

    child_resp = await async_client.post(
        "/api/folders/",
        json={
            "name": "Child",
            "parent_id": parent_id,
        },
    )
    assert child_resp.status_code == 201
    assert child_resp.json()["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_list_folders(async_client):
    await async_client.post("/api/folders/", json={"name": "Folder A"})
    await async_client.post("/api/folders/", json={"name": "Folder B"})

    response = await async_client.get("/api/folders/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_rename_folder(async_client):
    resp = await async_client.post("/api/folders/", json={"name": "Old Name"})
    folder_id = resp.json()["id"]

    response = await async_client.patch(
        f"/api/folders/{folder_id}", json={"name": "New Name"}
    )
    assert response.status_code == 200

    get_resp = await async_client.get(f"/api/folders/{folder_id}")
    assert get_resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_folder(async_client):
    resp = await async_client.post("/api/folders/", json={"name": "To Delete"})
    folder_id = resp.json()["id"]

    response = await async_client.delete(f"/api/folders/{folder_id}")
    assert response.status_code == 200

    # After delete, the folder must not appear in listings.
    listing = await async_client.get("/api/folders/")
    assert listing.json() == []


@pytest.mark.asyncio
async def test_get_folder_not_found(async_client):
    response = await async_client.get(
        "/api/folders/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "folder_not_found"


# ==================== File Tests ====================


@pytest.mark.asyncio
async def test_upload_file(async_client):
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test.txt"
    assert data["size"] == 11
    assert "id" in data


@pytest.mark.asyncio
async def test_list_files(async_client):
    await async_client.post(
        "/api/files/upload",
        files={"file": ("file1.txt", b"content1", "text/plain")},
    )
    await async_client.post(
        "/api/files/upload",
        files={"file": ("file2.txt", b"content2", "text/plain")},
    )

    response = await async_client.get("/api/files/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["files"]) >= 2


@pytest.mark.asyncio
async def test_folder_listing_returns_recursive_folder_size(async_client):
    parent = await async_client.post("/api/folders/", json={"name": "Parent"})
    parent_id = parent.json()["id"]

    child = await async_client.post(
        "/api/folders/",
        json={"name": "Child", "parent_id": parent_id},
    )
    child_id = child.json()["id"]

    await async_client.post(
        "/api/files/upload",
        params={"folder_id": child_id},
        files={"file": ("nested.txt", b"hello world", "text/plain")},
    )

    listing = await async_client.get("/api/files/")
    assert listing.status_code == 200

    folder = next(item for item in listing.json()["folders"] if item["id"] == parent_id)
    assert folder["size"] == 11


@pytest.mark.asyncio
async def test_get_file_meta(async_client):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("meta.txt", b"metadata test", "text/plain")},
    )
    file_id = resp.json()["id"]

    response = await async_client.get(f"/api/files/{file_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "meta.txt"


@pytest.mark.asyncio
async def test_move_file(async_client):
    folder_resp = await async_client.post("/api/folders/", json={"name": "Target"})
    folder_id = folder_resp.json()["id"]

    file_resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("movable.txt", b"move me", "text/plain")},
    )
    file_id = file_resp.json()["id"]

    response = await async_client.post(
        f"/api/files/{file_id}/move",
        json={"folder_id": folder_id},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rename_file(async_client):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("old_name.txt", b"rename test", "text/plain")},
    )
    file_id = resp.json()["id"]

    response = await async_client.patch(
        f"/api/files/{file_id}/rename",
        json={"name": "new_name.txt"},
    )
    assert response.status_code == 200

    get_resp = await async_client.get(f"/api/files/{file_id}")
    assert get_resp.json()["name"] == "new_name.txt"


@pytest.mark.asyncio
async def test_delete_file_moves_to_trash(async_client, fake_minio):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("deletable.txt", b"delete me", "text/plain")},
    )
    file_id = resp.json()["id"]
    # We don't need the file's minio_object_id here — the API doesn't
    # expose it (and exposing it would be a leak).  Just confirm the
    # delete succeeds.
    delete = await async_client.delete(f"/api/files/{file_id}")
    assert delete.status_code == 200

    # The file should be invisible through normal listings.
    listing = await async_client.get("/api/files/")
    assert all(item["id"] != file_id for item in listing.json()["files"])

    # But it should appear in the trash.
    trash = await async_client.get("/api/trash/")
    assert any(item["id"] == file_id for item in trash.json())


# ==================== Trash Tests ====================


@pytest.mark.asyncio
async def test_trash_list(async_client):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("trash_test.txt", b"trash me", "text/plain")},
    )
    file_id = resp.json()["id"]
    await async_client.delete(f"/api/files/{file_id}")

    response = await async_client.get("/api/trash/")
    assert response.status_code == 200
    data = response.json()
    assert any(item["id"] == file_id for item in data)


@pytest.mark.asyncio
async def test_restore_from_trash(async_client):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("restore_test.txt", b"restore me", "text/plain")},
    )
    file_id = resp.json()["id"]
    await async_client.delete(f"/api/files/{file_id}")

    response = await async_client.post(f"/api/trash/{file_id}/restore")
    assert response.status_code == 200

    get_resp = await async_client.get(f"/api/files/{file_id}")
    assert get_resp.status_code == 200


# ==================== Search Tests ====================


@pytest.mark.asyncio
async def test_search(async_client):
    await async_client.post(
        "/api/files/upload",
        files={"file": ("report_q1.pdf", b"pdf content", "application/pdf")},
    )
    await async_client.post(
        "/api/files/upload",
        files={"file": ("invoice_2024.pdf", b"invoice", "application/pdf")},
    )

    response = await async_client.get("/api/search/?q=report")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any("report" in item["name"] for item in data["results"])


# ==================== Quota Tests ====================


@pytest.mark.asyncio
async def test_quota(async_client):
    response = await async_client.get("/api/files/quota")
    assert response.status_code == 200
    data = response.json()
    assert "used" in data
    assert "total" in data
    assert "percent" in data


# ==================== Security: Auth ====================


@pytest.mark.asyncio
async def test_unauthorized_without_token(async_client, override_get_db, fake_minio):
    """The dependency override is removed — request must hit the real auth."""
    app.dependency_overrides.pop(get_current_user_id, None)
    try:
        response = await async_client.get("/api/files/")
        assert response.status_code == 401
        assert response.json()["error"] == "unauthenticated"
    finally:
        # Restore the default override for any later tests sharing the fixture.
        switch_user(USER_ALICE)


@pytest.mark.asyncio
async def test_refresh_token_rejected_for_data_api(
    async_client, override_get_db, fake_minio
):
    """A token with type=refresh must NOT be accepted on data endpoints."""
    app.dependency_overrides.pop(get_current_user_id, None)
    try:
        token = make_jwt(USER_ALICE, token_type="refresh", secret=settings.jwt_secret)
        response = await async_client.get(
            "/api/files/", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
        assert response.json()["error"] == "unauthenticated"
    finally:
        switch_user(USER_ALICE)


# ==================== Security: IDOR (cross-tenant access) ====================


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_file(async_client, fake_minio):
    # Alice uploads a file.
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("alice.txt", b"alice content", "text/plain")},
    )
    file_id = resp.json()["id"]

    # Bob attempts to read it.
    switch_user(USER_BOB)
    response = await async_client.get(f"/api/files/{file_id}")
    assert response.status_code == 404

    # Bob also cannot download, rename, move, delete, restore.
    assert (await async_client.get(f"/api/files/{file_id}/download")).status_code == 404
    assert (await async_client.delete(f"/api/files/{file_id}")).status_code == 404
    assert (
        await async_client.patch(
            f"/api/files/{file_id}/rename", json={"name": "pwned.txt"}
        )
    ).status_code == 404

    # Switch back to Alice and confirm the file is still hers.
    switch_user(USER_ALICE)
    assert (await async_client.get(f"/api/files/{file_id}")).status_code == 200


@pytest.mark.asyncio
async def test_user_cannot_list_another_users_folders(async_client):
    await async_client.post("/api/folders/", json={"name": "Alice's Secrets"})

    switch_user(USER_BOB)
    listing = await async_client.get("/api/folders/")
    assert listing.status_code == 200
    assert listing.json() == []


# ==================== Security: Upload validation ====================


@pytest.mark.asyncio
async def test_oversized_upload_rejected(async_client):
    from src.config import settings

    payload = b"x" * (settings.max_upload_size + 1)
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("big.bin", payload, "application/octet-stream")},
    )
    assert response.status_code == 413
    assert response.json()["error"] == "payload_too_large"


@pytest.mark.asyncio
async def test_dangerous_extension_rejected(async_client):
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("malware.exe", b"MZ\x00\x00", "application/octet-stream")},
    )
    assert response.status_code == 415
    assert response.json()["error"] == "unsupported_file_type"


@pytest.mark.asyncio
async def test_html_upload_rejected(async_client):
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("page.html", b"<script>alert(1)</script>", "text/html")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_filename_path_traversal_sanitized(async_client):
    """``../../etc/passwd`` should be sanitized to ``passwd`` and saved under
    a name that does not contain path separators."""
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("../../etc/passwd", b"hello", "text/plain")},
    )
    # Extension is missing after sanitization -> 415 unsupported_file_type.
    # That's the safe outcome: we never let the path through.
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_filename_with_path_separators_sanitized(async_client):
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("C:\\Users\\admin\\evil.txt", b"ok", "text/plain")},
    )
    # The "drive letter" prefix has no extension, so 415 is the safe path.
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_filename_nul_byte_stripped(async_client):
    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("good.txt\x00.exe", b"ok", "text/plain")},
    )
    # NUL byte must be removed before whitelist check; the remaining
    # ".txt" passes, so we should see a successful upload with a
    # sanitized name.
    assert response.status_code == 201
    assert "\x00" not in response.json()["name"]


# ==================== Security: Folder cycles ====================


@pytest.mark.asyncio
async def test_folder_move_cycle_rejected(async_client):
    parent = await async_client.post("/api/folders/", json={"name": "Parent"})
    parent_id = parent.json()["id"]
    child = await async_client.post(
        "/api/folders/", json={"name": "Child", "parent_id": parent_id}
    )
    child_id = child.json()["id"]

    # Try to move Parent into Child — this would create a cycle.
    response = await async_client.patch(
        f"/api/folders/{parent_id}", json={"parent_id": child_id}
    )
    assert response.status_code == 409
    assert response.json()["error"] == "cycle_detected"


@pytest.mark.asyncio
async def test_deep_folder_move_cycle_rejected(async_client):
    a = (await async_client.post("/api/folders/", json={"name": "A"})).json()
    b = (
        await async_client.post(
            "/api/folders/", json={"name": "B", "parent_id": a["id"]}
        )
    ).json()
    c = (
        await async_client.post(
            "/api/folders/", json={"name": "C", "parent_id": b["id"]}
        )
    ).json()

    # Try to move A under C — C is a descendant of A.
    response = await async_client.patch(
        f"/api/folders/{a['id']}", json={"parent_id": c["id"]}
    )
    assert response.status_code == 409


# ==================== Security: Soft delete visibility ====================


@pytest.mark.asyncio
async def test_soft_deleted_file_not_in_listing(async_client):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("secret.txt", b"hidden", "text/plain")},
    )
    file_id = resp.json()["id"]
    await async_client.delete(f"/api/files/{file_id}")

    listing = await async_client.get("/api/files/")
    assert all(item["id"] != file_id for item in listing.json()["files"])


@pytest.mark.asyncio
async def test_soft_deleted_file_not_downloadable(async_client, fake_minio):
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("private.txt", b"hidden", "text/plain")},
    )
    file_id = resp.json()["id"]
    await async_client.delete(f"/api/files/{file_id}")

    download = await async_client.get(f"/api/files/{file_id}/download")
    assert download.status_code == 404


# ==================== Security: Quota ====================


@pytest.mark.asyncio
async def test_quota_enforced(async_client, monkeypatch):

    # Shrink the quota to a tiny value to trigger 413 without uploading a lot.
    async def fake_quota(_user_id):
        return 100  # 100 bytes

    monkeypatch.setattr(quota_service, "get_storage_quota", fake_quota)

    response = await async_client.post(
        "/api/files/upload",
        files={"file": ("oversize.txt", b"x" * 200, "text/plain")},
    )
    assert response.status_code == 413
    assert response.json()["error"] == "quota_exceeded"


# ==================== Security: Quota race condition ====================


@pytest.mark.asyncio
async def test_concurrent_uploads_do_not_exceed_quota(async_client, monkeypatch):
    """Two concurrent uploads of 60 bytes each, with quota=100. Exactly
    one must succeed; the other must be rejected."""
    import asyncio

    async def fake_quota(_user_id):
        return 100

    monkeypatch.setattr(quota_service, "get_storage_quota", fake_quota)

    async def upload():
        return await async_client.post(
            "/api/files/upload",
            files={"file": ("r.txt", b"x" * 60, "text/plain")},
        )

    r1, r2 = await asyncio.gather(upload(), upload())
    statuses = sorted([r1.status_code, r2.status_code])
    assert statuses == [201, 413], f"Expected one success + one 413, got {statuses}"


# ==================== Security: Download ====================


@pytest.mark.asyncio
async def test_download_proxies_content(async_client, fake_minio):
    payload = b"streamed payload"
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("download.txt", payload, "text/plain")},
    )
    file_id = resp.json()["id"]

    r = await async_client.get(f"/api/files/{file_id}/download")
    assert r.status_code == 200
    assert r.content == payload
    # Content-Disposition with the safe filename
    cd = r.headers["content-disposition"]
    assert "download.txt" in cd
    # nosniff prevents MIME confusion attacks
    assert r.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_presigned_url_endpoint_removed(async_client):
    """Phase 1: the leaky /{file_id}/url endpoint is gone."""
    resp = await async_client.post(
        "/api/files/upload",
        files={"file": ("a.txt", b"x", "text/plain")},
    )
    file_id = resp.json()["id"]
    r = await async_client.get(f"/api/files/{file_id}/url")
    assert r.status_code in (404, 405)
