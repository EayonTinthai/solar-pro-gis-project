"""
Server-managed demo lifecycle using Clerk private/public metadata.

Sensitive and idempotency fields live in private metadata.
Frontend-safe fields are mirrored into public metadata.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import jwt
import requests
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from jwt import InvalidTokenError, PyJWKClient
from pydantic import BaseModel, Field
from svix.webhooks import Webhook, WebhookVerificationError
import os

DEMO_STATUS_NONE = "none"
DEMO_STATUS_PENDING = "pending"
DEMO_STATUS_GRANTED = "granted"
DEMO_STATUS_EXPIRED = "expired"
ALLOWED_DEMO_STATUSES = {
    DEMO_STATUS_NONE,
    DEMO_STATUS_PENDING,
    DEMO_STATUS_GRANTED,
    DEMO_STATUS_EXPIRED,
}
ALLOWED_PLANS = {"free", "pro"}
DEFAULT_DEMO_DURATION_DAYS = 14
DEFAULT_AUTO_LOGIN_TRIAL_DAYS = 7
CLERK_API_BASE = "https://api.clerk.com/v1"

demo_lifecycle_router = APIRouter(tags=["demo-access"])


class DemoAccessRequestBody(BaseModel):
    source: str = Field(..., min_length=1, max_length=200)
    company: Optional[str] = Field(default=None, max_length=200)
    note: Optional[str] = Field(default=None, max_length=4000)


class TourCompleteBody(BaseModel):
    completed: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_or_none(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _add_days_iso(iso_value: str, days: int) -> Optional[str]:
    dt = _parse_iso(iso_value)
    if dt is None:
        return None
    return (dt + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _normalize_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def _normalize_status(value: Any) -> str:
    return value if value in ALLOWED_DEMO_STATUSES else DEMO_STATUS_NONE


def _normalize_plan(value: Any) -> str:
    return value if value in ALLOWED_PLANS else "free"


def _duration_days() -> int:
    raw = os.getenv("DEMO_DURATION_DAYS", str(DEFAULT_DEMO_DURATION_DAYS))
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_DEMO_DURATION_DAYS
    return parsed if parsed > 0 else DEFAULT_DEMO_DURATION_DAYS


def _auto_login_trial_days() -> int:
    raw = os.getenv("DEMO_AUTO_LOGIN_TRIAL_DAYS", str(DEFAULT_AUTO_LOGIN_TRIAL_DAYS))
    try:
        parsed = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_AUTO_LOGIN_TRIAL_DAYS
    return parsed if parsed > 0 else DEFAULT_AUTO_LOGIN_TRIAL_DAYS


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing required environment variable: {name}")
    return value


@lru_cache(maxsize=4)
def _get_jwks_client(issuer: str) -> PyJWKClient:
    jwks_url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def _decode_clerk_token(token: str) -> Dict[str, Any]:
    issuer = _required_env("CLERK_JWT_ISSUER")
    jwks_client = _get_jwks_client(issuer)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=issuer,
        options={"verify_aud": False},
    )


def _extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1].strip()


def _auth_user_id(authorization: Optional[str] = Header(default=None)) -> str:
    token = _extract_bearer_token(authorization)
    try:
        payload = _decode_clerk_token(token)
    except (InvalidTokenError, Exception):
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise HTTPException(status_code=401, detail="Token missing user id")
    return user_id


def _clerk_api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {_required_env('CLERK_SECRET_KEY')}",
        "Content-Type": "application/json",
    }


def _clerk_api_request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    base = os.getenv("CLERK_API_BASE", CLERK_API_BASE).strip().rstrip("/")
    url = f"{base}{path}"
    try:
        response = requests.request(
            method,
            url,
            headers=_clerk_api_headers(),
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Clerk API request failed: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text
        try:
            parsed = response.json()
            detail = parsed.get("errors") or parsed.get("message") or parsed
        except ValueError:
            pass
        raise HTTPException(status_code=502, detail=f"Clerk API error ({response.status_code}): {detail}")

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Clerk API returned non-JSON response") from exc


def _clerk_get_user(user_id: str) -> Dict[str, Any]:
    return _clerk_api_request("GET", f"/users/{user_id}")


def _clerk_patch_user(
    user_id: str,
    private_metadata: Dict[str, Any],
    public_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    return _clerk_api_request(
        "PATCH",
        f"/users/{user_id}",
        payload={
            "private_metadata": private_metadata,
            "public_metadata": public_metadata,
        },
    )


def _primary_email(user: Dict[str, Any]) -> Optional[str]:
    addresses = user.get("email_addresses")
    if not isinstance(addresses, list):
        return None
    primary_id = user.get("primary_email_address_id")
    if isinstance(primary_id, str):
        for address in addresses:
            if not isinstance(address, dict):
                continue
            if address.get("id") == primary_id:
                email = _normalize_text(address.get("email_address"))
                if email:
                    return email
    for address in addresses:
        if not isinstance(address, dict):
            continue
        email = _normalize_text(address.get("email_address"))
        if email:
            return email
    return None


def _display_name(user: Dict[str, Any]) -> str:
    first = _normalize_text(user.get("first_name"))
    last = _normalize_text(user.get("last_name"))
    if first and last:
        return f"{first} {last}"
    if first:
        return first
    if last:
        return last
    username = _normalize_text(user.get("username"))
    if username:
        return username
    return "User"


def _normalize_state(private_metadata: Dict[str, Any], public_metadata: Dict[str, Any]) -> Dict[str, Any]:
    private_root = private_metadata if isinstance(private_metadata, dict) else {}
    public_root = public_metadata if isinstance(public_metadata, dict) else {}

    private_demo = private_root.get("demo_access")
    private_demo = private_demo if isinstance(private_demo, dict) else {}
    public_demo = public_root.get("demo_access")
    public_demo = public_demo if isinstance(public_demo, dict) else {}

    private_onboarding = private_root.get("onboarding")
    private_onboarding = private_onboarding if isinstance(private_onboarding, dict) else {}
    public_onboarding = public_root.get("onboarding")
    public_onboarding = public_onboarding if isinstance(public_onboarding, dict) else {}

    private_plan = private_root.get("plan")
    if private_plan not in ALLOWED_PLANS:
        private_plan = public_root.get("plan")
    plan = _normalize_plan(private_plan)

    return {
        "plan": plan,
        "demo_access": {
            "status": _normalize_status(private_demo.get("status") or public_demo.get("status")),
            "requested_at": _iso_or_none(private_demo.get("requested_at")),
            "requested_source": _normalize_text(private_demo.get("requested_source")),
            "company": _normalize_text(private_demo.get("company")),
            "note": _normalize_text(private_demo.get("note")),
            "granted_at": _iso_or_none(private_demo.get("granted_at")),
            "expires_at": _iso_or_none(private_demo.get("expires_at") or public_demo.get("expires_at")),
            "expired_at": _iso_or_none(private_demo.get("expired_at") or public_demo.get("expired_at")),
            "pending_email_sent_at": _iso_or_none(private_demo.get("pending_email_sent_at")),
            "team_notified_at": _iso_or_none(private_demo.get("team_notified_at")),
            "granted_email_sent_at": _iso_or_none(private_demo.get("granted_email_sent_at")),
            "expired_email_sent_at": _iso_or_none(private_demo.get("expired_email_sent_at")),
        },
        "onboarding": {
            "tour_completed_at": _iso_or_none(
                private_onboarding.get("tour_completed_at") or public_onboarding.get("tour_completed_at")
            ),
        },
    }


def _public_mirror_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    demo = state["demo_access"]
    onboarding = state["onboarding"]
    return {
        "plan": _normalize_plan(state["plan"]),
        "demo_access": {
            "status": _normalize_status(demo["status"]),
            "expires_at": _iso_or_none(demo["expires_at"]),
            "expired_at": _iso_or_none(demo["expired_at"]),
        },
        "onboarding": {
            "tour_completed_at": _iso_or_none(onboarding["tour_completed_at"]),
        },
    }


def _status_payload_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    demo = state["demo_access"]
    return {
        "plan": _normalize_plan(state["plan"]),
        "demo_access": {
            "status": _normalize_status(demo["status"]),
            "requested_at": _iso_or_none(demo["requested_at"]),
            "granted_at": _iso_or_none(demo["granted_at"]),
            "expires_at": _iso_or_none(demo["expires_at"]),
            "expired_at": _iso_or_none(demo["expired_at"]),
        },
        "onboarding": {
            "tour_completed_at": _iso_or_none(state["onboarding"]["tour_completed_at"]),
        },
    }


def _mirror_needs_update(public_metadata: Dict[str, Any], state: Dict[str, Any]) -> bool:
    current = _normalize_state({}, public_metadata)
    mirror = _public_mirror_from_state(state)
    expected = _normalize_state({}, mirror)
    return current["plan"] != expected["plan"] or current["demo_access"] != expected["demo_access"] or current[
        "onboarding"
    ] != expected["onboarding"]


def _is_granted_active(state: Dict[str, Any]) -> bool:
    demo = state["demo_access"]
    if demo["status"] != DEMO_STATUS_GRANTED:
        return False
    expires_at = _parse_iso(demo["expires_at"])
    if expires_at is None:
        return True
    return expires_at > datetime.now(timezone.utc)


def _enforce_transitions(state: Dict[str, Any]) -> bool:
    changed = False
    now_iso = _now_iso()
    now_dt = _parse_iso(now_iso)
    demo = state["demo_access"]

    if demo["status"] == DEMO_STATUS_GRANTED:
        if not demo["granted_at"]:
            demo["granted_at"] = now_iso
            changed = True
        if not demo["expires_at"]:
            expires = _add_days_iso(demo["granted_at"], _duration_days())
            if expires:
                demo["expires_at"] = expires
                changed = True
        expires_dt = _parse_iso(demo["expires_at"])
        if expires_dt and now_dt and expires_dt <= now_dt:
            if demo["status"] != DEMO_STATUS_EXPIRED:
                demo["status"] = DEMO_STATUS_EXPIRED
                changed = True
            if not demo["expired_at"]:
                demo["expired_at"] = now_iso
                changed = True
            if state["plan"] != "free":
                state["plan"] = "free"
                changed = True
        elif state["plan"] != "pro":
            state["plan"] = "pro"
            changed = True
    elif demo["status"] == DEMO_STATUS_EXPIRED:
        if not demo["expired_at"]:
            demo["expired_at"] = now_iso
            changed = True
        if state["plan"] != "free":
            state["plan"] = "free"
            changed = True
    elif demo["status"] == DEMO_STATUS_PENDING:
        if state["plan"] != "free":
            state["plan"] = "free"
            changed = True

    return changed


def _auto_grant_login_trial(state: Dict[str, Any]) -> bool:
    demo = state["demo_access"]

    # One-time login trial for brand-new users only.
    if demo["status"] != DEMO_STATUS_NONE:
        return False
    if demo["requested_at"] or demo["granted_at"] or demo["expired_at"]:
        return False

    granted_at = _now_iso()
    expires_at = _add_days_iso(granted_at, _auto_login_trial_days())

    demo["status"] = DEMO_STATUS_GRANTED
    demo["requested_at"] = None
    demo["requested_source"] = "auto_login_trial"
    demo["company"] = None
    demo["note"] = None
    demo["granted_at"] = granted_at
    demo["expires_at"] = expires_at
    demo["expired_at"] = None
    demo["pending_email_sent_at"] = None
    demo["team_notified_at"] = None
    demo["granted_email_sent_at"] = None
    demo["expired_email_sent_at"] = None
    state["plan"] = "pro"
    return True


def _send_resend_email(to_email: str, subject: str, text_body: str) -> Tuple[bool, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("DEMO_EMAIL_FROM", "").strip()
    if not api_key or not from_email:
        return False, "resend_not_configured"

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": text_body,
    }
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        return False, f"resend_request_error:{exc}"

    if response.status_code >= 400:
        return False, f"resend_http_{response.status_code}"
    return True, ""


def _send_pending_user_email(state: Dict[str, Any], user: Dict[str, Any], warnings: list[str]) -> bool:
    email = _primary_email(user)
    if not email:
        warnings.append("pending_user_email_skipped_missing_email")
        return False
    demo = state["demo_access"]
    requested_label = demo["requested_at"] or _now_iso()
    subject = "Demo access request received"
    body = (
        "We received your demo access request.\n\n"
        f"Requested at: {requested_label}\n"
        "Status: pending\n\n"
        "Our team will review and notify you once access is granted."
    )
    ok, reason = _send_resend_email(email, subject, body)
    if not ok:
        warnings.append(f"pending_user_email_failed:{reason}")
    return ok


def _send_pending_team_email(state: Dict[str, Any], user: Dict[str, Any], warnings: list[str]) -> bool:
    team_inbox = os.getenv("DEMO_TEAM_INBOX", "").strip()
    if not team_inbox:
        warnings.append("pending_team_email_skipped_missing_team_inbox")
        return False
    user_email = _primary_email(user) or "unknown"
    user_name = _display_name(user)
    demo = state["demo_access"]
    subject = f"New demo access request: {user_email}"
    body = (
        "A user requested demo access.\n\n"
        f"User: {user_name}\n"
        f"Email: {user_email}\n"
        f"Requested at: {demo['requested_at'] or _now_iso()}\n"
        f"Source: {demo['requested_source'] or 'N/A'}\n"
        f"Company: {demo['company'] or 'N/A'}\n"
        f"Note: {demo['note'] or 'N/A'}"
    )
    ok, reason = _send_resend_email(team_inbox, subject, body)
    if not ok:
        warnings.append(f"pending_team_email_failed:{reason}")
    return ok


def _send_granted_email(state: Dict[str, Any], user: Dict[str, Any], warnings: list[str]) -> bool:
    email = _primary_email(user)
    if not email:
        warnings.append("granted_email_skipped_missing_email")
        return False
    demo = state["demo_access"]
    subject = "Demo access granted"
    body = (
        "Your demo access is now active.\n\n"
        f"Granted at: {demo['granted_at'] or _now_iso()}\n"
        f"Expires at: {demo['expires_at'] or 'N/A'}\n"
        "Plan: Pro"
    )
    ok, reason = _send_resend_email(email, subject, body)
    if not ok:
        warnings.append(f"granted_email_failed:{reason}")
    return ok


def _send_expired_email(state: Dict[str, Any], user: Dict[str, Any], warnings: list[str]) -> bool:
    email = _primary_email(user)
    if not email:
        warnings.append("expired_email_skipped_missing_email")
        return False
    demo = state["demo_access"]
    subject = "Demo access expired"
    body = (
        "Your demo access has expired and your account is now on the Free plan.\n\n"
        f"Expired at: {demo['expired_at'] or _now_iso()}"
    )
    ok, reason = _send_resend_email(email, subject, body)
    if not ok:
        warnings.append(f"expired_email_failed:{reason}")
    return ok


def _load_user_state(user_id: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    user = _clerk_get_user(user_id)
    private_metadata = deepcopy(user.get("private_metadata") or {})
    public_metadata = deepcopy(user.get("public_metadata") or {})
    state = _normalize_state(private_metadata, public_metadata)
    return user, private_metadata, public_metadata, state


def _persist_state(
    user_id: str,
    private_metadata: Dict[str, Any],
    public_metadata: Dict[str, Any],
    state: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    next_private = deepcopy(private_metadata)
    next_private["plan"] = state["plan"]
    next_private["demo_access"] = deepcopy(state["demo_access"])
    next_private["onboarding"] = deepcopy(state["onboarding"])

    mirror = _public_mirror_from_state(state)
    next_public = deepcopy(public_metadata)
    next_public["plan"] = mirror["plan"]
    next_public["demo_access"] = mirror["demo_access"]
    next_public["onboarding"] = mirror["onboarding"]

    patched = _clerk_patch_user(
        user_id=user_id,
        private_metadata=next_private,
        public_metadata=next_public,
    )
    patched_private = deepcopy(patched.get("private_metadata") or {})
    patched_public = deepcopy(patched.get("public_metadata") or {})
    patched_state = _normalize_state(patched_private, patched_public)
    return patched, patched_private, patched_public, patched_state


def _verify_clerk_webhook(headers: Dict[str, str], payload: bytes) -> Dict[str, Any]:
    secret = _required_env("CLERK_WEBHOOK_SECRET")
    svix_headers = {
        "svix-id": headers.get("svix-id"),
        "svix-timestamp": headers.get("svix-timestamp"),
        "svix-signature": headers.get("svix-signature"),
    }
    if not all(svix_headers.values()):
        raise HTTPException(status_code=400, detail="Missing Svix webhook signature headers")
    webhook = Webhook(secret)
    try:
        event = webhook.verify(payload, svix_headers)
    except WebhookVerificationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid webhook signature: {exc}") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    return event


@demo_lifecycle_router.post("/demo-access/request")
def request_demo_access(body: DemoAccessRequestBody, user_id: str = Depends(_auth_user_id)):
    user, private_metadata, public_metadata, state = _load_user_state(user_id)
    state_changed = _enforce_transitions(state)

    if state_changed or _mirror_needs_update(public_metadata, state):
        user, private_metadata, public_metadata, state = _persist_state(
            user_id, private_metadata, public_metadata, state
        )

    if state["demo_access"]["status"] == DEMO_STATUS_PENDING:
        payload = _status_payload_from_state(state)
        payload.update({"ok": True, "code": "already_pending"})
        return payload

    if _is_granted_active(state):
        payload = _status_payload_from_state(state)
        payload.update(
            {
                "ok": True,
                "code": "already_granted",
            }
        )
        return payload

    now_iso = _now_iso()
    demo = state["demo_access"]
    demo["status"] = DEMO_STATUS_PENDING
    demo["requested_at"] = now_iso
    demo["requested_source"] = _normalize_text(body.source) or "Locked Pro feature"
    demo["company"] = _normalize_text(body.company)
    demo["note"] = _normalize_text(body.note)
    demo["granted_at"] = None
    demo["expires_at"] = None
    demo["expired_at"] = None
    demo["pending_email_sent_at"] = None
    demo["team_notified_at"] = None
    demo["granted_email_sent_at"] = None
    demo["expired_email_sent_at"] = None
    state["plan"] = "free"

    user, private_metadata, public_metadata, state = _persist_state(
        user_id, private_metadata, public_metadata, state
    )

    warnings: list[str] = []
    markers_changed = False
    if not state["demo_access"]["pending_email_sent_at"] and _send_pending_user_email(state, user, warnings):
        state["demo_access"]["pending_email_sent_at"] = _now_iso()
        markers_changed = True
    if not state["demo_access"]["team_notified_at"] and _send_pending_team_email(state, user, warnings):
        state["demo_access"]["team_notified_at"] = _now_iso()
        markers_changed = True

    if markers_changed:
        user, private_metadata, public_metadata, state = _persist_state(
            user_id, private_metadata, public_metadata, state
        )

    payload = _status_payload_from_state(state)
    payload.update(
        {
            "ok": True,
            "code": "requested",
            "email_warnings": warnings,
        }
    )
    return payload


@demo_lifecycle_router.get("/demo-access/status")
def get_demo_access_status(user_id: str = Depends(_auth_user_id)):
    user, private_metadata, public_metadata, state = _load_user_state(user_id)

    auto_granted = _auto_grant_login_trial(state)
    state_changed = _enforce_transitions(state) or auto_granted
    warnings: list[str] = []
    markers_changed = False
    demo = state["demo_access"]

    if demo["status"] == DEMO_STATUS_PENDING:
        if not demo["pending_email_sent_at"] and _send_pending_user_email(state, user, warnings):
            demo["pending_email_sent_at"] = _now_iso()
            markers_changed = True
        if not demo["team_notified_at"] and _send_pending_team_email(state, user, warnings):
            demo["team_notified_at"] = _now_iso()
            markers_changed = True
    elif demo["status"] == DEMO_STATUS_GRANTED:
        if not demo["granted_email_sent_at"] and _send_granted_email(state, user, warnings):
            demo["granted_email_sent_at"] = _now_iso()
            markers_changed = True
    elif demo["status"] == DEMO_STATUS_EXPIRED:
        if not demo["expired_email_sent_at"] and _send_expired_email(state, user, warnings):
            demo["expired_email_sent_at"] = _now_iso()
            markers_changed = True

    if state_changed or markers_changed or _mirror_needs_update(public_metadata, state):
        user, private_metadata, public_metadata, state = _persist_state(
            user_id, private_metadata, public_metadata, state
        )

    payload = _status_payload_from_state(state)
    if warnings:
        payload["warnings"] = warnings
    return payload


@demo_lifecycle_router.post("/demo-access/onboarding-tour/complete")
def complete_onboarding_tour(body: TourCompleteBody, user_id: str = Depends(_auth_user_id)):
    if not body.completed:
        raise HTTPException(status_code=400, detail="`completed` must be true")

    user, private_metadata, public_metadata, state = _load_user_state(user_id)
    code = "already_completed"
    if not state["onboarding"]["tour_completed_at"]:
        state["onboarding"]["tour_completed_at"] = _now_iso()
        code = "completed"

    if code == "completed" or _mirror_needs_update(public_metadata, state):
        user, private_metadata, public_metadata, state = _persist_state(
            user_id, private_metadata, public_metadata, state
        )

    payload = _status_payload_from_state(state)
    payload.update({"ok": True, "code": code})
    return payload


@demo_lifecycle_router.post("/webhooks/clerk")
async def clerk_webhook(request: Request):
    payload = await request.body()
    event = _verify_clerk_webhook(request.headers, payload)
    event_type = event.get("type")
    if event_type != "user.updated":
        return {"ok": True, "ignored": event_type}

    data = event.get("data")
    data = data if isinstance(data, dict) else {}
    user_id = data.get("id")
    if not isinstance(user_id, str) or not user_id.strip():
        return {"ok": True, "ignored": "missing_user_id"}

    user, private_metadata, public_metadata, state = _load_user_state(user_id)
    demo = state["demo_access"]
    if demo["status"] != DEMO_STATUS_GRANTED:
        return {"ok": True, "ignored": "status_not_granted"}

    state_changed = False
    if not demo["granted_at"]:
        demo["granted_at"] = _now_iso()
        state_changed = True
    if not demo["expires_at"]:
        expires = _add_days_iso(demo["granted_at"], _duration_days())
        if expires:
            demo["expires_at"] = expires
            state_changed = True
    if state["plan"] != "pro":
        state["plan"] = "pro"
        state_changed = True

    warnings: list[str] = []
    markers_changed = False
    if not demo["granted_email_sent_at"] and _send_granted_email(state, user, warnings):
        demo["granted_email_sent_at"] = _now_iso()
        markers_changed = True

    if state_changed or markers_changed or _mirror_needs_update(public_metadata, state):
        user, private_metadata, public_metadata, state = _persist_state(
            user_id, private_metadata, public_metadata, state
        )

    return {
        "ok": True,
        "processed": True,
        "warnings": warnings,
    }
