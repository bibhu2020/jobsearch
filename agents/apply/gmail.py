"""Reads verification codes / links from the user's Gmail (gmail.readonly)."""
import asyncio
import base64
import html
import os
import re
import time

import httpx

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://gmail.googleapis.com/gmail/v1/users/me"

CODE_RE = re.compile(r"(?:code|pin|otp|passcode)[^0-9A-Za-z]{0,40}([A-Z0-9]{4,8})\b|\b(\d{6})\b", re.I)
LINK_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
VERIFY_WORDS = re.compile(r"verif|confirm|activat|validate", re.I)


class GmailAuthError(Exception):
    """The refresh token was revoked or expired (Google expires them after 7 days in testing mode)."""


async def access_token(refresh_token: str) -> str:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(TOKEN_URL, data={
            "client_id": os.environ["GOOGLE_OAUTH_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_OAUTH_CLIENT_SECRET"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
        if resp.status_code in (400, 401) and resp.json().get("error") in ("invalid_grant", "unauthorized_client"):
            raise GmailAuthError(resp.json().get("error"))
        resp.raise_for_status()
        return resp.json()["access_token"]


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def _body_text(payload: dict) -> str:
    parts = [payload] + payload.get("parts", [])
    chunks: list[str] = []
    while parts:
        p = parts.pop(0)
        parts.extend(p.get("parts", []))
        data = p.get("body", {}).get("data")
        if data and p.get("mimeType", "").startswith("text/"):
            chunks.append(_decode(data))
    return "\n".join(chunks)


def extract_code_or_link(text: str) -> dict | None:
    """Prefer an explicit verification link; otherwise a code near the word code/pin/otp."""
    unescaped = html.unescape(text)
    for link in LINK_RE.findall(unescaped):
        if VERIFY_WORDS.search(link) and "unsubscribe" not in link.lower():
            return {"link": link.rstrip(").,")}
    plain = re.sub(r"<[^>]+>", " ", unescaped)
    m = CODE_RE.search(plain)
    if m:
        return {"code": m.group(1) or m.group(2)}
    return None


async def wait_for_verification(refresh_token: str, sender_domain: str, since_epoch: float,
                                timeout_s: int = 180, interval_s: int = 10) -> dict | None:
    """Poll Gmail for a message from `sender_domain` received after `since_epoch`."""
    token = await access_token(refresh_token)
    headers = {"Authorization": f"Bearer {token}"}
    deadline = time.time() + timeout_s
    seen: set[str] = set()
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        while time.time() < deadline:
            resp = await client.get(f"{API}/messages", params={"q": f"from:{sender_domain} newer_than:1h", "maxResults": 5})
            resp.raise_for_status()
            for ref in resp.json().get("messages", []):
                if ref["id"] in seen:
                    continue
                seen.add(ref["id"])
                msg = (await client.get(f"{API}/messages/{ref['id']}", params={"format": "full"})).json()
                if int(msg.get("internalDate", 0)) / 1000 < since_epoch - 30:
                    continue
                found = extract_code_or_link(_body_text(msg.get("payload", {})))
                if found:
                    return found
            await asyncio.sleep(interval_s)
    return None
