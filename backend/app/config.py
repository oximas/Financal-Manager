from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql://pfm_user:pfm_pass@localhost:5432/pfm_db"

    # JWT
    jwt_secret_key: str = "dev_secret_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080  # 7 days

    # App
    app_env: str = "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
