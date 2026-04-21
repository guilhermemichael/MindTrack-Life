import time


_cache: dict[str, tuple[object, float | None]] = {}


def get(key: str):
    cached = _cache.get(key)
    if cached is None:
        return None

    value, expires_at = cached
    if expires_at is not None and expires_at < time.time():
        _cache.pop(key, None)
        return None
    return value


def set(key: str, value, ttl: int | None = 45):
    expires_at = None if ttl in (None, 0) else time.time() + ttl
    _cache[key] = (value, expires_at)
    return value


def invalidate(key: str):
    _cache.pop(key, None)


def invalidate_prefix(prefix: str):
    for key in list(_cache):
        if key.startswith(prefix):
            _cache.pop(key, None)
