"""
Model Intelligence System (MIS) v1 - Model Catalog and Sync Engine.

This module provides:
- Model catalog database (stores OpenRouter models)
- Sync engine (fetches and normalizes OpenRouter models)
- Update mode settings (auto, notify, off)
- Diff tracking (new, updated, removed models)
"""
import sqlite3
import json
import threading
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from codecompanion.settings import settings


OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


@dataclass
class ModelInfo:
    """
    Represents a model from the catalog.

    Attributes:
        id: Model identifier (e.g., "anthropic/claude-3.5-sonnet")
        provider: Provider name (e.g., "openrouter")
        display_name: Human-readable model name
        family: Model family (e.g., "claude", "gpt", "llama")
        context_length: Maximum context tokens
        input_price: USD per 1M input tokens
        output_price: USD per 1M output tokens
        capabilities: JSON dict of capabilities (vision, tools, etc.)
        is_active: Whether model is currently available
        created_at: ISO timestamp when first added
        updated_at: ISO timestamp when last updated
    """
    id: str
    provider: str
    display_name: Optional[str] = None
    family: Optional[str] = None
    context_length: Optional[int] = None
    input_price: Optional[float] = None
    output_price: Optional[float] = None
    capabilities: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert capabilities dict to JSON string for storage
        if self.capabilities:
            data['capabilities'] = json.dumps(self.capabilities)
        return data

    @staticmethod
    def from_row(row: sqlite3.Row) -> 'ModelInfo':
        """Create ModelInfo from database row."""
        capabilities = None
        if row['capabilities']:
            try:
                capabilities = json.loads(row['capabilities'])
            except (json.JSONDecodeError, TypeError):
                capabilities = {}

        return ModelInfo(
            id=row['id'],
            provider=row['provider'],
            display_name=row['display_name'],
            family=row['family'],
            context_length=row['context_length'],
            input_price=row['input_price'],
            output_price=row['output_price'],
            capabilities=capabilities,
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )


class ModelCatalogStore:
    """
    Thread-safe SQLite-based storage for model catalog.

    Manages three tables:
    - model_catalog: Model information
    - model_catalog_meta: Per-provider sync metadata
    - model_settings: Feature settings (e.g., update_mode)
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize model catalog store.

        Args:
            db_path: Path to SQLite database. Defaults to .cc/jobs.db
        """
        if db_path is None:
            db_path = Path.cwd() / ".cc" / "jobs.db"

        self.db_path = db_path
        self._lock = threading.Lock()
        self._ensure_schema()

    def _ensure_schema(self):
        """Initialize database schema for model catalog."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            # Create model_catalog table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_catalog (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    display_name TEXT,
                    family TEXT,
                    context_length INTEGER,
                    input_price REAL,
                    output_price REAL,
                    capabilities TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create model_catalog_meta table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_catalog_meta (
                    provider TEXT PRIMARY KEY,
                    last_synced TEXT
                )
            """)

            # Create model_settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS model_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Create indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_catalog_provider
                ON model_catalog(provider)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_catalog_is_active
                ON model_catalog(is_active)
            """)

            conn.commit()

    @contextmanager
    def _get_conn(self):
        """Get thread-safe database connection."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def upsert_model(self, model: ModelInfo) -> ModelInfo:
        """
        Insert or update a model in the catalog.

        Args:
            model: ModelInfo to upsert

        Returns:
            The upserted ModelInfo
        """
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO model_catalog (
                    id, provider, display_name, family, context_length,
                    input_price, output_price, capabilities, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                model.id,
                model.provider,
                model.display_name,
                model.family,
                model.context_length,
                model.input_price,
                model.output_price,
                json.dumps(model.capabilities) if model.capabilities else None,
                1 if model.is_active else 0,
                model.created_at,
                model.updated_at,
            ))
            conn.commit()

        return model

    def mark_inactive(self, model_id: str) -> bool:
        """
        Mark a model as inactive.

        Args:
            model_id: Model ID to mark inactive

        Returns:
            True if model was found and updated
        """
        with self._get_conn() as conn:
            now = datetime.utcnow().isoformat() + "Z"
            cursor = conn.execute("""
                UPDATE model_catalog
                SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (now, model_id))
            conn.commit()
            return cursor.rowcount > 0

    def list_models(self, provider: Optional[str] = None, active_only: bool = False) -> List[ModelInfo]:
        """
        List models from catalog.

        Args:
            provider: Filter by provider (optional)
            active_only: Only return active models

        Returns:
            List of ModelInfo objects
        """
        with self._get_conn() as conn:
            query = "SELECT * FROM model_catalog WHERE 1=1"
            params = []

            if provider:
                query += " AND provider = ?"
                params.append(provider)

            if active_only:
                query += " AND is_active = 1"

            query += " ORDER BY display_name ASC"

            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            return [ModelInfo.from_row(row) for row in rows]

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get a specific model by ID.

        Args:
            model_id: Model identifier

        Returns:
            ModelInfo if found, None otherwise
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM model_catalog WHERE id = ?",
                (model_id,)
            )
            row = cursor.fetchone()

            if row:
                return ModelInfo.from_row(row)
            return None

    def get_last_synced(self, provider: str) -> Optional[str]:
        """
        Get last sync timestamp for a provider.

        Args:
            provider: Provider name

        Returns:
            ISO timestamp or None if never synced
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT last_synced FROM model_catalog_meta WHERE provider = ?",
                (provider,)
            )
            row = cursor.fetchone()

            if row and row['last_synced']:
                return row['last_synced']
            return None

    def set_last_synced(self, provider: str, timestamp: str):
        """
        Set last sync timestamp for a provider.

        Args:
            provider: Provider name
            timestamp: ISO timestamp
        """
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO model_catalog_meta (provider, last_synced)
                VALUES (?, ?)
            """, (provider, timestamp))
            conn.commit()

    def get_update_mode(self) -> str:
        """
        Get current update mode setting.

        Returns:
            "auto", "notify", or "off" (default: "notify")
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT value FROM model_settings WHERE key = ?",
                ("model_update_mode",)
            )
            row = cursor.fetchone()

            if row:
                return row['value']
            return "notify"  # Default

    def set_update_mode(self, mode: str):
        """
        Set update mode setting.

        Args:
            mode: One of "auto", "notify", or "off"

        Raises:
            ValueError: If mode is invalid
        """
        if mode not in ("auto", "notify", "off"):
            raise ValueError(f"Invalid update mode: {mode}. Must be 'auto', 'notify', or 'off'")

        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO model_settings (key, value)
                VALUES (?, ?)
            """, ("model_update_mode", mode))
            conn.commit()


# ==============================================================================
# OpenRouter Model Fetcher & Sync Engine
# ==============================================================================


def fetch_openrouter_models(api_key: str) -> List[dict]:
    """
    Fetch current models from OpenRouter API.

    Args:
        api_key: OpenRouter API key

    Returns:
        List of raw model dictionaries from API

    Raises:
        httpx.HTTPError: If API request fails
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "HTTP-Referer": "https://github.com/AidiJackson/codecompanion",
        "X-Title": "CodeCompanion",
    }

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(OPENROUTER_MODELS_URL, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    # OpenRouter returns {"data": [...]}
    return data.get("data", [])


def normalize_openrouter_model(raw: dict) -> ModelInfo:
    """
    Normalize OpenRouter API model data to ModelInfo.

    Converts pricing to USD per 1M tokens (matching PROVIDER_PRICING format).

    Args:
        raw: Raw model dict from OpenRouter API

    Returns:
        Normalized ModelInfo object
    """
    model_id = raw.get("id", "")
    display_name = raw.get("name") or model_id

    # Extract family (may not be provided by OpenRouter)
    family = None
    if "/" in model_id:
        family = model_id.split("/")[0]  # e.g., "anthropic" from "anthropic/claude-3.5-sonnet"

    # Extract pricing (OpenRouter may provide per-token or per-1K prices)
    # Normalize to USD per 1M tokens
    pricing = raw.get("pricing", {})
    input_price = None
    output_price = None

    if "prompt" in pricing:
        # Assume pricing is in USD per token, convert to per 1M
        input_price = float(pricing["prompt"]) * 1_000_000

    if "completion" in pricing:
        output_price = float(pricing["completion"]) * 1_000_000

    # Extract context length
    context_length = raw.get("context_length")

    # Extract capabilities
    capabilities = {
        "vision": raw.get("architecture", {}).get("modality") == "multimodal" if "architecture" in raw else False,
        "tools": raw.get("top_provider", {}).get("is_moderated", False) if "top_provider" in raw else False,
    }

    now = datetime.utcnow().isoformat() + "Z"

    return ModelInfo(
        id=model_id,
        provider="openrouter",
        display_name=display_name,
        family=family,
        context_length=context_length,
        input_price=input_price,
        output_price=output_price,
        capabilities=capabilities,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def sync_openrouter_models() -> Dict[str, Any]:
    """
    Fetch current OpenRouter models, sync them into catalog, and return diff.

    Returns:
        Dict with:
            - provider: "openrouter"
            - new: List of new model IDs
            - updated: List of updated model IDs
            - removed: List of removed model IDs
            - last_synced: ISO timestamp

    Raises:
        RuntimeError: If OPENROUTER_API_KEY is not set
        httpx.HTTPError: If API request fails
    """
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    store = ModelCatalogStore()

    # 1. Fetch current remote models
    raw_models = fetch_openrouter_models(api_key)
    normalized = [normalize_openrouter_model(m) for m in raw_models]

    # 2. Get existing models from catalog
    existing = {m.id: m for m in store.list_models(provider="openrouter")}
    seen_ids = set()
    new_ids = []
    updated_ids = []

    # 3. Upsert new/updated models
    for model in normalized:
        seen_ids.add(model.id)

        if model.id not in existing:
            # New model
            store.upsert_model(model)
            new_ids.append(model.id)
        else:
            # Check if model changed
            old = existing[model.id]
            if (
                old.input_price != model.input_price
                or old.output_price != model.output_price
                or old.context_length != model.context_length
                or old.family != model.family
                or old.display_name != model.display_name
            ):
                # Update existing (preserve created_at)
                model.created_at = old.created_at
                store.upsert_model(model)
                updated_ids.append(model.id)

    # 4. Mark removed models as inactive
    removed_ids = []
    for model_id, old in existing.items():
        if model_id not in seen_ids and old.is_active:
            store.mark_inactive(model_id)
            removed_ids.append(model_id)

    # 5. Update last_synced timestamp
    now = datetime.utcnow().isoformat() + "Z"
    store.set_last_synced("openrouter", now)

    return {
        "provider": "openrouter",
        "new": new_ids,
        "updated": updated_ids,
        "removed": removed_ids,
        "last_synced": now,
    }


# ==============================================================================
# Global Catalog Store Instance
# ==============================================================================

_catalog_store: Optional[ModelCatalogStore] = None


def get_catalog_store(db_path: Optional[Path] = None) -> ModelCatalogStore:
    """
    Get global model catalog store instance.

    Args:
        db_path: Optional path to database file

    Returns:
        ModelCatalogStore instance
    """
    global _catalog_store

    if _catalog_store is None:
        _catalog_store = ModelCatalogStore(db_path)

    return _catalog_store
