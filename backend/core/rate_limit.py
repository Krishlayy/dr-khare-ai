from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.config import settings

limiter_kwargs = {"key_func": get_remote_address}
if settings.REDIS_URL:
    limiter_kwargs["storage_uri"] = settings.REDIS_URL

limiter = Limiter(**limiter_kwargs)
