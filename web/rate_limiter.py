import time
import hashlib
from collections import defaultdict

MAX_CONVERSIONS = 30
COOLDOWN_SECONDS = 30 * 60

_client_data: dict[str, dict] = defaultdict(lambda: {"count": 0, "window_start": 0})


def _get_client_id(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else request.client.host or "unknown"
    ua = request.headers.get("user-agent", "")
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def check_rate_limit(request) -> dict:
    cid = _get_client_id(request)
    now = time.time()
    client = _client_data[cid]

    if now - client["window_start"] > COOLDOWN_SECONDS:
        client["count"] = 0
        client["window_start"] = now

    remaining = MAX_CONVERSIONS - client["count"]
    cooldown_until = 0
    if remaining <= 0:
        cooldown_until = client["window_start"] + COOLDOWN_SECONDS

    return {
        "allowed": remaining > 0,
        "remaining": max(0, remaining),
        "limit": MAX_CONVERSIONS,
        "cooldown_seconds": max(0, int(cooldown_until - now)) if cooldown_until else 0,
    }


def record_conversion(request):
    cid = _get_client_id(request)
    now = time.time()
    client = _client_data[cid]

    if now - client["window_start"] > COOLDOWN_SECONDS:
        client["count"] = 0
        client["window_start"] = now

    client["count"] += 1


def get_rate_info(request) -> dict:
    info = check_rate_limit(request)
    return {
        "remaining": info["remaining"],
        "limit": info["limit"],
        "cooldown": info["cooldown_seconds"],
    }
