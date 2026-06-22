"""Start the Warmth FastAPI server from the flat gtmhackathon repo layout.

Imports use the ``warmth.apps.*`` package path; this bootstrap registers that
namespace when ``apps/`` lives at the repo root (not under ``warmth/``).
"""
from __future__ import annotations

import importlib.util
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except Exception:
    pass


def _register_package(name: str, path: Path) -> types.ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    mod = types.ModuleType(name)
    mod.__path__ = [str(path)]
    mod.__package__ = name
    sys.modules[name] = mod
    return mod


def _load_main() -> object:
    _register_package("warmth", ROOT)
    _register_package("warmth.apps", ROOT / "apps")
    _register_package("warmth.apps.api", ROOT / "apps" / "api")
    _register_package("warmth.packages", ROOT / "packages")
    _register_package("warmth.infra", ROOT / "infra")
    _register_package("warmth.services", ROOT / "services")

    main_path = ROOT / "apps" / "api" / "main.py"
    spec = importlib.util.spec_from_file_location(
        "warmth.apps.api.main",
        main_path,
        submodule_search_locations=[str(main_path.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load API module from {main_path}")

    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "warmth.apps.api"
    sys.modules["warmth.apps.api.main"] = mod
    spec.loader.exec_module(mod)
    return mod.app


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8010"))
    host = os.getenv("API_HOST", "0.0.0.0")
    _load_main()
    uvicorn.run("warmth.apps.api.main:app", host=host, port=port, reload=True)
