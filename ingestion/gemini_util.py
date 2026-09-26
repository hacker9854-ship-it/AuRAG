"""Shared Gemini call wrapper with quota spacing and transient retries."""

import time

_MIN_INTERVAL = 13.0
_RETRY_DELAYS = (5.0, 15.0, 30.0)
_last_call = 0.0


def throttled_generate(client, **kwargs):
    global _last_call

    for attempt in range(len(_RETRY_DELAYS) + 1):
        wait = _MIN_INTERVAL - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()

        try:
            return client.models.generate_content(**kwargs)
        except Exception as exc:
            transient = any(
                marker in str(exc)
                for marker in (
                    "RESOURCE_EXHAUSTED",
                    "UNAVAILABLE",
                    "high demand",
                    "429",
                    "503",
                )
            )
            if not transient or attempt >= len(_RETRY_DELAYS):
                raise
            time.sleep(_RETRY_DELAYS[attempt])
