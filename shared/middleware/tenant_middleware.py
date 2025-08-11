from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp
from typing import Optional, Dict

# NOTE: Replace this stub with real JWT verification (e.g. python-jose, authlib, etc.)
# Keep this stub minimal so it works without extra deps.

def _parse_bearer_token(auth_header: Optional[str]) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def verify_and_decode_jwt(token: str) -> Dict:
    """Stub: decode/verify token and return claims.
    In production, verify signature, issuer, audience, expiry, etc.
    Return a dict with at least a 'tenant_id' key.
    """
    # For now, just a placeholder. MUST be replaced with real verification.
    # Example fallback: accept a raw JSON string token for local testing.
    import json
    try:
        return json.loads(token)
    except Exception:
        return {"tenant_id": "default"}


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts tenant_id from JWT and attaches it to request.state.tenant_id.
    Falls back to 'default' when missing.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        token = _parse_bearer_token(request.headers.get("Authorization"))
        if token:
            claims = verify_and_decode_jwt(token)
            request.state.tenant_id = claims.get("tenant_id", "default")
        else:
            request.state.tenant_id = "default"
        return await call_next(request)