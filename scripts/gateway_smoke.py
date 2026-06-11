from __future__ import annotations

import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


BASE_URL = os.environ.get("CFS_BASE_URL", "http://localhost:8080")
API_BASE = f"{BASE_URL}/api"
HEALTH_ENDPOINTS = (
    "/health",
    "/health/auth",
    "/health/file",
    "/health/preview",
)


class SmokeFailure(RuntimeError):
    pass


def log(step: str, detail: str) -> None:
    print(f"[smoke] {step}: {detail}")


def request_json(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 20,
) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return response.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            parsed = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            parsed = {"raw": payload}
        return exc.code, parsed


def request_health(path: str, timeout: int = 10) -> tuple[int, str]:
    request = urllib.request.Request(f"{BASE_URL}{path}", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def build_multipart_body(
    *,
    field_name: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> tuple[bytes, str]:
    boundary = f"----cfs-smoke-{uuid.uuid4().hex}"
    lines = [
        f"--{boundary}".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename}"'
        ).encode("utf-8"),
        f"Content-Type: {content_type}".encode("utf-8"),
        b"",
        content,
        f"--{boundary}--".encode("utf-8"),
        b"",
    ]
    return b"\r\n".join(lines), boundary


def upload_file(
    *,
    token: str,
    folder_id: str | None,
    filename: str,
    content: bytes,
) -> tuple[int, dict]:
    query = ""
    if folder_id:
        query = f"?folder_id={urllib.parse.quote(folder_id)}"

    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body, boundary = build_multipart_body(
        field_name="file",
        filename=filename,
        content=content,
        content_type=content_type,
    )
    request = urllib.request.Request(
        f"{API_BASE}/files/upload{query}",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            parsed = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            parsed = {"raw": payload}
        return exc.code, parsed


def request_bytes(path: str, *, token: str, timeout: int = 20) -> tuple[int, bytes]:
    request = urllib.request.Request(
        f"{API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def expect(status: int, expected: int | tuple[int, ...], detail: str) -> None:
    allowed = expected if isinstance(expected, tuple) else (expected,)
    if status not in allowed:
        raise SmokeFailure(f"{detail}: expected {allowed}, got {status}")


def wait_for_health() -> None:
    deadline = time.time() + 90
    pending = set(HEALTH_ENDPOINTS)
    while pending and time.time() < deadline:
        for endpoint in list(pending):
            status, _ = request_health(endpoint)
            if status == 200:
                log("health", f"{endpoint} OK")
                pending.remove(endpoint)
        if pending:
            time.sleep(2)

    if pending:
        raise SmokeFailure(f"health endpoints not ready: {', '.join(sorted(pending))}")


def main() -> int:
    suffix = uuid.uuid4().hex[:10]
    email = f"smoke-{suffix}@example.com"
    password = "smoke-password-123"
    folder_name = f"smoke-folder-{suffix}"
    upload_name = f"smoke-{suffix}.txt"
    upload_bytes = f"hello from smoke {suffix}\n".encode("utf-8")

    log("target", BASE_URL)
    wait_for_health()

    status, registered = request_json(
        "POST",
        "/auth/register",
        body={
            "email": email,
            "password": password,
            "full_name": "Gateway Smoke",
        },
    )
    expect(status, 201, "register")
    access_token = registered["access_token"]
    log("register", email)

    status, me = request_json("GET", "/auth/me", token=access_token)
    expect(status, 200, "get current user")
    if me["email"] != email:
        raise SmokeFailure(f"unexpected /me email: {me['email']}")
    log("me", "profile loaded")

    status, verification = request_json(
        "POST",
        "/auth/verify-email/request",
        token=access_token,
    )
    expect(status, 200, "request verify email")
    verification_token = verification.get("token")
    if not verification_token:
        raise SmokeFailure("verify-email/request did not return token")

    status, verify_result = request_json(
        "GET",
        f"/auth/verify-email?token={urllib.parse.quote(verification_token)}",
    )
    expect(status, 200, "consume verify email token")
    if verify_result.get("verified") is not True:
        raise SmokeFailure("verify-email did not verify the user")
    log("verify", "email verified")

    status, folder = request_json(
        "POST",
        "/folders/",
        token=access_token,
        body={"name": folder_name, "parent_id": None},
    )
    expect(status, 201, "create folder")
    folder_id = folder["id"]
    log("folder", folder_name)

    status, uploaded = upload_file(
        token=access_token,
        folder_id=folder_id,
        filename=upload_name,
        content=upload_bytes,
    )
    expect(status, 201, "upload file")
    file_id = uploaded["id"]
    log("upload", upload_name)

    status, search = request_json(
        "GET",
        f"/search/?q={urllib.parse.quote(suffix)}",
        token=access_token,
    )
    expect(status, 200, "search")
    if not any(item["id"] == file_id for item in search.get("results", [])):
        raise SmokeFailure("uploaded file not found in search results")
    log("search", f"{search.get('total', 0)} result(s)")

    status, payload = request_bytes(f"/files/{file_id}/download", token=access_token)
    expect(status, 200, "download file")
    if payload != upload_bytes:
        raise SmokeFailure("downloaded bytes do not match uploaded bytes")
    log("download", "content verified")

    status, moved = request_json("DELETE", f"/files/{file_id}", token=access_token)
    expect(status, 200, "move file to trash")
    log("trash", moved.get("status", "moved"))

    status, trash_items = request_json("GET", "/trash/", token=access_token)
    expect(status, 200, "list trash")
    if not any(item["id"] == file_id for item in trash_items):
        raise SmokeFailure("trashed file not listed in trash")

    status, restored = request_json("POST", f"/trash/{file_id}/restore", token=access_token)
    expect(status, 200, "restore from trash")
    log("restore", restored.get("status", "restored"))

    status, moved_again = request_json("DELETE", f"/files/{file_id}", token=access_token)
    expect(status, 200, "move file to trash again")
    status, deleted = request_json("DELETE", f"/trash/{file_id}/permanent", token=access_token)
    expect(status, 200, "permanent delete")
    log("delete", deleted.get("status", "deleted permanently"))

    status, forgot = request_json(
        "POST",
        "/auth/forgot-password",
        body={"email": email},
    )
    expect(status, 200, "forgot password")
    reset_token = forgot.get("token")
    if not reset_token:
        raise SmokeFailure("forgot-password did not return reset token")

    new_password = "smoke-password-456"
    status, reset_result = request_json(
        "POST",
        "/auth/reset-password",
        body={"token": reset_token, "new_password": new_password},
    )
    expect(status, 200, "reset password")
    log("reset", reset_result.get("message", "ok"))

    status, logged_in = request_json(
        "POST",
        "/auth/login",
        body={"email": email, "password": new_password},
    )
    expect(status, 200, "login with reset password")

    current_refresh_token = logged_in["refresh_token"]

    status, logout = request_json(
        "POST",
        "/auth/logout",
        body={"refresh_token": current_refresh_token},
    )
    expect(status, 200, "logout")

    status, refreshed = request_json(
        "POST",
        "/auth/refresh",
        token=current_refresh_token,
    )
    if status == 200:
        raise SmokeFailure("refresh token still worked after logout")
    expect(status, 401, "refresh after logout should fail")
    log("logout", "refresh token revoked")

    print("[smoke] PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"[smoke] FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
