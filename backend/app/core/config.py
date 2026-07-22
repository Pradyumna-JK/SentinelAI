"""Centralized application configuration.

Every value is sourced from environment variables (prefix ``SENTINEL_``) or a
local ``.env`` file for host development. Credential fields are declared
without defaults on purpose: the application refuses to start if they are
missing, and there is never a secret literal in the codebase. Values wrapped
in ``SecretStr`` are additionally masked in reprs and logs.
"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Application ---
    app_name: str = "SentinelAI Backend"
    app_version: str = "0.2.0"
    environment: str = "development"

    # --- Logging ---
    log_level: str = "INFO"
    # None = auto: JSON logs everywhere except the "development" environment.
    log_json: bool | None = None

    # --- CORS ---
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # --- PostgreSQL ---
    # Either set DATABASE_URL directly (no SENTINEL_ prefix — a conventional,
    # widely-recognized name so the same var works with generic tooling), or
    # leave it unset and let `database_url` build the DSN from the discrete
    # fields below. docker-compose.yml uses the discrete fields, since Compose
    # already injects each credential separately; DATABASE_URL is for
    # environments (CI, PaaS platforms) that hand you a single connection
    # string instead.
    database_url_override: str | None = Field(default=None, validation_alias="DATABASE_URL")
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    # Optional here (unlike redis/minio credentials below) because they're
    # only *conditionally* required — see the `database_url` property, which
    # raises a clear error at first use if neither this trio nor
    # DATABASE_URL was provided.
    postgres_user: str | None = None
    postgres_password: SecretStr | None = None
    postgres_db: str | None = None
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # `postgres_user` above (e.g. "sentinel") owns the schema and runs
    # migrations — in this stack it's also a Postgres superuser, which means
    # it *always* bypasses Row-Level Security, FORCE or not. If the running
    # application connected as that same role, RLS would be a no-op for it
    # too — a fact-check step, not a real backstop. app_db_user/password are
    # a second, unprivileged, non-owner role (created by the RLS migration,
    # see alembic/versions/*_tenant_isolation_rls.py) that RLS *does*
    # restrict; the runtime engine (app/core/database.py) connects as this
    # role, while Alembic (alembic/env.py) keeps using the owner role above.
    # Left unset, `app_database_url` falls back to the owner credentials —
    # migrations still work, but RLS stops being a real second layer, only
    # the ORM-level filter remains. Fine for a quick local spike; not for
    # anything that matters.
    app_db_user: str | None = None
    app_db_password: SecretStr | None = None

    # A third role, used *only* by AuthService's pre-authentication flows
    # (login by email; refresh/password-reset by stored token) — the one
    # legitimate case where queries against the RLS-guarded `users` table
    # must run *before* a tenant context can possibly exist, since
    # establishing that context is exactly what these flows do. This role
    # has BYPASSRLS but is deliberately not superuser, and its grants are
    # narrowed to the auth domain: users, refresh_tokens,
    # password_reset_tokens, and read-only RBAC tables (roles/permissions/
    # associations, needed to build the token's claims). It has NO access
    # to factories/sites/buildings/zones — so a bug in code using it can
    # never leak another tenant's business data. `sentinel_app` itself
    # never gets BYPASSRLS: that would silently disable RLS for every
    # other service's queries too, not just this one necessary exception.
    auth_db_user: str | None = None
    auth_db_password: SecretStr | None = None

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr

    # --- MinIO (S3-compatible object storage) ---
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str
    minio_secret_key: SecretStr
    minio_secure: bool = False
    minio_bucket: str = "sentinel-evidence"

    # --- Vision inference engine (app/ai/vision) ---
    # Directory holding the ONNX weight files listed in
    # app/ai/vision/registry.py. Missing files degrade that specific
    # capability rather than failing startup — see engine.py's `start()`.
    vision_models_dir: str = "models/vision"
    # Global floor confidence; per-class overrides in registry.py win when set.
    vision_min_confidence: float = 0.4
    # Max frames per ONNX call. Larger = better GPU throughput, higher
    # per-frame latency for whichever frame arrives first in the window.
    vision_batch_size: int = 8
    # How long the worker waits to fill a batch before running it partial —
    # bounds worst-case latency when frames trickle in below vision_batch_size.
    vision_batch_window_ms: int = 50
    # Process every Nth frame per source; the rest resolve as SKIPPED
    # without spending any CPU/GPU time. 1 = process every frame.
    vision_frame_skip: int = 1
    # Bounded queue depth across all sources combined; beyond this, new
    # frames resolve as DROPPED (drop-newest) instead of blocking the
    # producer — see engine.py's module docstring for why that's correct
    # for live video specifically.
    vision_queue_size: int = 64

    # --- Risk Intelligence Engine (app/ai/risk) ---
    # How fast an individual hazard event's contribution fades — 15 min
    # means a fire seen 15 min ago counts for half of one seen just now.
    risk_decay_half_life_seconds: int = 900
    # How much concurrent OTHER active hazards add on top of the single
    # worst one when aggregating a zone's raw score (see scoring.py's
    # aggregate_events). 0 = only the worst hazard ever matters.
    risk_compound_boost_factor: float = 0.25
    # EWMA smoothing weight for the score time series; 1.0 disables
    # smoothing (score == this instant's raw aggregate).
    risk_rolling_average_alpha: float = 0.3
    # How far ahead predicted_score forecasts, via linear regression over
    # recent snapshots (see scoring.py's predict_and_trend).
    risk_prediction_horizon_minutes: float = 15.0
    # Slope magnitude (score points per minute) below which trend reads as
    # "stable" rather than increasing/decreasing — filters regression noise.
    risk_trend_deadband_per_minute: float = 0.5
    # Hazard events older than this are excluded from a zone's risk
    # computation entirely, decayed or not.
    risk_event_lookback_minutes: int = 60
    # How many trailing snapshots feed the trend/prediction regression.
    risk_history_window_for_trend: int = 12
    # How often the background scheduler (app/ai/risk/scheduler.py)
    # recomputes + persists a snapshot for every zone with recent events.
    risk_recompute_interval_seconds: int = 30

    # --- Sensor/IoT simulation (app/ai/sensors) ---
    # No real hardware exists for this demo — see simulator.py's module
    # docstring for why this writes a legible buildup-and-clear narrative
    # rather than pure noise.
    sensor_simulation_interval_seconds: int = 15

    # --- Compound Risk Intelligence Engine (app/ai/compound_risk) ---
    # How often the background scheduler re-runs the signal-fusion graph
    # per zone and persists a finding into the existing RiskEvent pipeline.
    compound_risk_recompute_interval_seconds: int = 20

    # --- Compliance Copilot (app/ai/compliance) ---
    # No default: same rationale as jwt_secret_key — refuse to start rather
    # than silently running with no LLM access. Embeddings and chat share
    # this one key/account; there's no operational reason to split them.
    # Model names use the "-latest" alias, not a pinned version — Google
    # retires pinned model names on a rolling basis (gemini-2.5-flash 404s
    # for new users as of writing). The embedding model needs the "models/"
    # prefix; the chat model does not — this is a Google API quirk, not a
    # typo.
    gemini_api_key: SecretStr
    gemini_chat_model: str = "gemini-flash-latest"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    # ChromaDB runs as its own container (docker-compose.yml's `chroma`
    # service) rather than an embedded/persistent client in-process, the
    # same reasoning as Postgres/Redis/MinIO each being their own service:
    # the vector store's lifecycle shouldn't be tied to the API container's.
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    # Character-based, not token-based — simpler, and RecursiveCharacterTextSplitter
    # tries paragraph/sentence boundaries first regardless of the unit used.
    compliance_chunk_size: int = 1200
    compliance_chunk_overlap: int = 150
    compliance_retrieval_top_k: int = 5
    # Cosine similarity (1 - distance) below which a retrieved chunk is
    # discarded as noise rather than passed to the LLM as context — see
    # app/ai/compliance/graph.py's `_retrieve` node.
    compliance_min_relevance_score: float = 0.35
    # How many trailing persisted turns feed conversation memory into the
    # next generation call — see app/ai/compliance/memory.py.
    compliance_history_window: int = 8
    compliance_max_upload_mb: int = 25

    # --- Auth (JWT) ---
    # No default: a fixed/shared secret in source would let anyone forge
    # tokens. HS256 is a single symmetric secret, appropriate for this
    # single-service monolith; move to RS256 + a JWKS endpoint if/when
    # other services need to verify tokens without holding the signing key.
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 30

    # --- Auth rate limiting (Redis-backed, see app/core/rate_limit.py) ---
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15
    max_password_reset_requests: int = 3
    password_reset_throttle_minutes: int = 60

    # --- RBAC bootstrap ---
    # Read once by the Alembic seed migration (alembic/versions/*_seed_rbac.py)
    # to create the first Admin account and default organization — never by
    # the running application. Left unset, the migration skips admin
    # creation rather than falling back to a hardcoded credential.
    default_organization_name: str = "SentinelAI Demo"
    default_organization_slug: str = "sentinelai-demo"
    admin_email: str | None = None
    admin_password: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SENTINEL_",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy DSN (also used by Alembic's async env).

        Prefers ``DATABASE_URL`` when set; otherwise builds an asyncpg DSN
        from the discrete ``postgres_*`` fields. Raises at first use (not at
        import time) if neither is sufficient, so a misconfigured deployment
        fails with an explicit message instead of a confusing driver error.
        """
        if self.database_url_override:
            return self.database_url_override
        if not (self.postgres_user and self.postgres_password and self.postgres_db):
            raise ValueError(
                "No database configuration found: set DATABASE_URL, or all of "
                "SENTINEL_POSTGRES_USER / SENTINEL_POSTGRES_PASSWORD / "
                "SENTINEL_POSTGRES_DB."
            )
        password = quote_plus(self.postgres_password.get_secret_value())
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def app_database_url(self) -> str:
        """DSN for the running application's own engine — see the
        `app_db_user`/`app_db_password` docstring above for why this is
        deliberately not always the same role as `database_url`.
        """
        if self.database_url_override:
            # An externally-supplied DATABASE_URL has no separate "app role"
            # concept to fall back to — it's already a complete connection.
            return self.database_url_override
        if self.app_db_user and self.app_db_password:
            if not (self.postgres_db and self.postgres_host):
                raise ValueError("SENTINEL_APP_DB_USER/PASSWORD set but POSTGRES_DB/HOST are not.")
            password = quote_plus(self.app_db_password.get_secret_value())
            return (
                f"postgresql+asyncpg://{self.app_db_user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self.database_url

    @property
    def auth_database_url(self) -> str:
        """DSN for AuthService's pre-authentication user lookups — see the
        `auth_db_user`/`auth_db_password` docstring above.
        """
        if self.database_url_override:
            return self.database_url_override
        if self.auth_db_user and self.auth_db_password:
            if not (self.postgres_db and self.postgres_host):
                raise ValueError("SENTINEL_AUTH_DB_USER/PASSWORD set but POSTGRES_DB/HOST are not.")
            password = quote_plus(self.auth_db_password.get_secret_value())
            return (
                f"postgresql+asyncpg://{self.auth_db_user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self.database_url

    @property
    def log_json_resolved(self) -> bool:
        if self.log_json is not None:
            return self.log_json
        return self.environment != "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance so env vars are parsed only once."""
    return Settings()
