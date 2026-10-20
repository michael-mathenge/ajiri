from pathlib import Path


def application_tree(base):
    """Restrict a checkout as a whole; packaged /app must not imply all of /."""
    base = Path(base).resolve()
    return next((path for path in (base, *base.parents) if (path / '.git').exists()), base)
