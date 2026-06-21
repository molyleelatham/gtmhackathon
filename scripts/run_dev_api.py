"""Start the FastAPI dev server with the warmth package namespace (matches Cloud Run)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _ensure_warmth_namespace() -> None:
    if "warmth" in sys.modules:
        return
    init = _REPO_ROOT / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "warmth",
        init,
        submodule_search_locations=[str(_REPO_ROOT)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load warmth package")
    module = importlib.util.module_from_spec(spec)
    sys.modules["warmth"] = module
    spec.loader.exec_module(module)


def main() -> None:
    _ensure_warmth_namespace()
    import uvicorn

    uvicorn.run(
        "warmth.apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
