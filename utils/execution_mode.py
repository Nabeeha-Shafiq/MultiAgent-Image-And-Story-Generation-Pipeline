import os

def is_mock() -> bool:
    return os.getenv("EXECUTION_MODE", "MOCK").upper() == "MOCK"

def require_real(fn):
    """Decorator: only calls real API if EXECUTION_MODE=REAL"""
    def wrapper(*args, **kwargs):
        if is_mock():
            raise RuntimeError(
                f"[BLOCKED] Real API call attempted in MOCK mode. "
                f"Set EXECUTION_MODE=REAL to enable. Function: {fn.__name__}"
            )
        return fn(*args, **kwargs)
    return wrapper
