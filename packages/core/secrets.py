"""Team secret management via Google Secret Manager.

Instead of every developer copying a `.env` full of live API keys, secrets live
in **Google Secret Manager** for the shared GCP project. At startup the app pulls
them into the process environment, so all existing `os.getenv(...)` calls keep
working unchanged.

Resolution order (later wins only when `override=True`):
  1. Anything already in the real environment / local `.env` (developer override)
  2. Secrets fetched from Google Secret Manager

Auth uses Application Default Credentials (ADC):
  - Local dev:  `gcloud auth application-default login`
  - Prod/CI:    a service account (GOOGLE_APPLICATION_CREDENTIALS or workload identity)

Secret naming convention: the Secret Manager *secret id* equals the environment
variable name (Secret Manager allows letters, digits, `_` and `-`). An optional
`prefix` lets you namespace, e.g. prefix="WARMTH_" maps secret `WARMTH_TAVILY_API_KEY`
to env var `TAVILY_API_KEY`.

This module degrades gracefully: if the SDK is missing, no project is configured,
or credentials are unavailable, it logs a warning and leaves the environment as-is
so local `.env`-only development still works.
"""

import logging
import os
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

# Env vars that hold the GCP project id, in priority order.
_PROJECT_ENV_VARS = ("GCP_PROJECT_ID", "GOOGLE_CLOUD_PROJECT", "GCLOUD_PROJECT")

# Secrets loaded at API startup (allowlist — never load the full project).
API_SECRET_ALLOWLIST: tuple[str, ...] = (
    "FIREBASE_SERVICE_ACCOUNT_KEY",
    "TAVILY_API_KEY",
    "DEEPGRAM_API_KEY",
    "ZERO_CRM_API_KEY",
    "UNIFY_GTM_API_KEY",
    "CURSOR_SDK_API_KEY",
    "GOOGLE_MCP_CREDENTIALS",
    "LIGHTFERN_WEBHOOK_URL",
    "GCP_SERVICE_ACCOUNT_KEY",
)


def resolve_project_id(project_id: Optional[str] = None) -> Optional[str]:
    """Return the GCP project id from the argument or known env vars."""
    if project_id:
        return project_id
    for var in _PROJECT_ENV_VARS:
        value = os.getenv(var)
        if value:
            return value
    return None


class SecretManager:
    """Thin wrapper around the Google Secret Manager client."""

    def __init__(self, project_id: Optional[str] = None, prefix: str = ""):
        self.project_id = resolve_project_id(project_id)
        self.prefix = prefix
        if not self.project_id:
            raise ValueError(
                "No GCP project id configured. Set GCP_PROJECT_ID (or pass project_id)."
            )

        # Imported lazily so the package import doesn't hard-require the SDK.
        from google.cloud import secretmanager  # noqa: WPS433

        self._sm = secretmanager
        self._client = secretmanager.SecretManagerServiceClient()

    @property
    def _parent(self) -> str:
        return f"projects/{self.project_id}"

    def _secret_id_for(self, env_name: str) -> str:
        return f"{self.prefix}{env_name}"

    def _env_name_for(self, secret_id: str) -> str:
        if self.prefix and secret_id.startswith(self.prefix):
            return secret_id[len(self.prefix):]
        return secret_id

    def list_secret_ids(self) -> list[str]:
        """List secret ids in the project (filtered by prefix when set)."""
        ids: list[str] = []
        for secret in self._client.list_secrets(request={"parent": self._parent}):
            secret_id = secret.name.rsplit("/", 1)[-1]
            if self.prefix and not secret_id.startswith(self.prefix):
                continue
            ids.append(secret_id)
        return ids

    def get_secret(self, env_name: str, version: str = "latest") -> Optional[str]:
        """Fetch the value of a single secret by its env-var name."""
        secret_id = self._secret_id_for(env_name)
        name = f"{self._parent}/secrets/{secret_id}/versions/{version}"
        try:
            response = self._client.access_secret_version(request={"name": name})
        except Exception as exc:  # NotFound, PermissionDenied, etc.
            logger.warning("Could not access secret '%s': %s", secret_id, exc)
            return None
        return response.payload.data.decode("utf-8")

    def set_secret(self, env_name: str, value: str) -> None:
        """Create the secret if needed and add a new version with `value`."""
        secret_id = self._secret_id_for(env_name)
        secret_path = f"{self._parent}/secrets/{secret_id}"
        try:
            self._client.get_secret(request={"name": secret_path})
        except Exception:
            self._client.create_secret(
                request={
                    "parent": self._parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            logger.info("Created secret '%s'", secret_id)
        self._client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": value.encode("utf-8")},
            }
        )
        logger.info("Added new version to secret '%s'", secret_id)

    def load_into_env(
        self,
        names: Optional[Iterable[str]] = None,
        override: bool = False,
    ) -> list[str]:
        """Load secrets into os.environ. Returns the env-var names that were set.

        If `names` is None, every secret in the project (matching the prefix) is
        loaded. Existing env values are kept unless `override=True`.
        """
        if names is None:
            secret_ids = self.list_secret_ids()
        else:
            secret_ids = [self._secret_id_for(n) for n in names]

        loaded: list[str] = []
        for secret_id in secret_ids:
            env_name = self._env_name_for(secret_id)
            if not override and os.getenv(env_name):
                continue
            value = self.get_secret(env_name)
            if value is None:
                continue
            os.environ[env_name] = value
            loaded.append(env_name)
        return loaded


def load_secrets_into_env(
    project_id: Optional[str] = None,
    names: Optional[Iterable[str]] = None,
    prefix: str = "",
    override: bool = False,
) -> list[str]:
    """Best-effort: pull team secrets from Secret Manager into os.environ.

    Safe to call unconditionally at startup. Returns the list of env vars that
    were populated (empty if Secret Manager is unavailable or unconfigured).
    """
    if os.getenv("DISABLE_SECRET_MANAGER", "").lower() in ("1", "true", "yes"):
        logger.info("Secret Manager disabled via DISABLE_SECRET_MANAGER")
        return []

    try:
        manager = SecretManager(project_id=project_id, prefix=prefix)
    except ValueError as exc:
        logger.info("Skipping Secret Manager: %s", exc)
        return []
    except ImportError:
        logger.warning(
            "google-cloud-secret-manager not installed; "
            "relying on local environment / .env only."
        )
        return []

    try:
        loaded = manager.load_into_env(names=names, override=override)
    except Exception as exc:  # auth/network errors shouldn't crash startup
        logger.warning("Failed to load secrets from Secret Manager: %s", exc)
        return []

    if loaded:
        logger.info(
            "Loaded %d secret(s) from Secret Manager (project=%s): %s",
            len(loaded),
            manager.project_id,
            ", ".join(loaded),
        )
    return loaded
