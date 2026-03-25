"""
Shared version helpers.

El proyecto muestra la versión al usuario en formato `Vx.x.x`, pero algunas
herramientas del ecosistema Python esperan una versión semántica limpia sin el
prefijo `V` para metadata tipo PEP 440. Este módulo centraliza ambas vistas
para no duplicar reglas en GUI, scripts y empaquetado.
"""

from pathlib import Path


DEFAULT_VERSION = "V1.0.0"


def normalize_version(raw: str, default: str = DEFAULT_VERSION) -> str:
    """
    Return a bare semantic version like `1.6.0`.

    Args:
        raw: Input value that may come as `V1.6.0` or `1.6.0`.
        default: Fallback version when the source is empty.
    """
    candidate = (raw or '').strip() or default
    if candidate.lower().startswith('v'):
        candidate = candidate[1:]

    parts = candidate.split('.')
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError(f"Invalid version '{raw}'. Expected Vx.x.x or x.x.x")

    return '.'.join(parts)


def display_version(raw: str, default: str = DEFAULT_VERSION) -> str:
    """Return the canonical UI/release format `Vx.x.x`."""
    return f"V{normalize_version(raw, default)}"


def read_version_file(path: Path, default: str = DEFAULT_VERSION) -> str:
    """Read VERSION from disk and normalize it to the display format."""
    if not path.exists():
        return display_version(default)

    return display_version(path.read_text(encoding='utf-8').strip() or default)


def pep440_version(raw: str, default: str = DEFAULT_VERSION) -> str:
    """Return a packaging-safe version string without the leading `V`."""
    return normalize_version(raw, default)


def bump_version(raw: str, part: str) -> str:
    """
    Increment a semantic version and return it in canonical display format.

    Args:
        raw: Current version in `Vx.x.x` or `x.x.x`.
        part: `major`, `minor` or `patch`.
    """
    major, minor, patch = (int(token) for token in normalize_version(raw).split('.'))

    if part == 'major':
        major += 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor += 1
        patch = 0
    else:
        patch += 1

    return display_version(f"{major}.{minor}.{patch}")
