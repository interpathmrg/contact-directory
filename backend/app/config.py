from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Seguridad / JWT
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Azure Active Directory
    azure_client_id: str
    azure_tenant_id: str
    azure_client_secret: str
    azure_redirect_uri: str = "http://localhost/auth/callback"
    azure_scopes: str = "User.Read"

    # Aplicación
    environment: str = "development"
    log_level: str = "INFO"
    upload_max_size_mb: int = 10
    upload_dir: str = "/app/uploads"
    allowed_origins: str = "http://localhost"
    frontend_url: str = "http://localhost"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """URL síncrona para Alembic (usa psycopg2)."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
