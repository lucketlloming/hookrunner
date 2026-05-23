"""Parse retry configuration from a hook definition dict."""

from typing import Any, Dict, Optional

from hookrunner.retry import RetryPolicy

_DEFAULTS: Dict[str, Any] = {
    "max_attempts": 1,
    "delay_seconds": 0.0,
    "backoff_factor": 1.0,
}

_RETRYABLE_EXCEPTIONS = {
    "Exception": Exception,
    "OSError": OSError,
    "RuntimeError": RuntimeError,
    "IOError": IOError,
}


class RetryConfigError(Exception):
    """Raised when a retry block in the config is invalid."""


def parse_retry_policy(hook_cfg: Dict[str, Any]) -> Optional[RetryPolicy]:
    """Return a :class:`RetryPolicy` from *hook_cfg*, or ``None`` if absent.

    Expected YAML shape::

        hooks:
          pre-commit:
            - name: lint
              run: ./scripts/lint.sh
              retry:
                max_attempts: 3
                delay_seconds: 1.0
                backoff_factor: 2.0
    """
    retry_cfg = hook_cfg.get("retry")
    if not retry_cfg:
        return None

    if not isinstance(retry_cfg, dict):
        raise RetryConfigError(
            f"'retry' must be a mapping, got {type(retry_cfg).__name__}"
        )

    unknown = set(retry_cfg) - set(_DEFAULTS) - {"retry_on"}
    if unknown:
        raise RetryConfigError(f"Unknown retry keys: {sorted(unknown)}")

    max_attempts = int(retry_cfg.get("max_attempts", _DEFAULTS["max_attempts"]))
    delay_seconds = float(retry_cfg.get("delay_seconds", _DEFAULTS["delay_seconds"]))
    backoff_factor = float(retry_cfg.get("backoff_factor", _DEFAULTS["backoff_factor"]))

    retry_on_names = retry_cfg.get("retry_on", ["Exception"])
    if isinstance(retry_on_names, str):
        retry_on_names = [retry_on_names]

    retry_on = []
    for name in retry_on_names:
        exc_cls = _RETRYABLE_EXCEPTIONS.get(name)
        if exc_cls is None:
            raise RetryConfigError(f"Unsupported retry_on exception: '{name}'")
        retry_on.append(exc_cls)

    policy = RetryPolicy(
        max_attempts=max_attempts,
        delay_seconds=delay_seconds,
        backoff_factor=backoff_factor,
        retry_on=tuple(retry_on),
    )
    policy.validate()
    return policy
