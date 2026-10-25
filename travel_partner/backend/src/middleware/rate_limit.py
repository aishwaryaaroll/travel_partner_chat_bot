"""Per-client-IP rate limiting (in memory, single process)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import get_settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[get_settings().rate_limit_default],
    headers_enabled=False,
)
