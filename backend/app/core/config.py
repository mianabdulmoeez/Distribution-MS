from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///F:/DMS/backend/dms_dev.db"
    SECRET_KEY: str = "dms-super-secret-key-for-local-development-must-be-long-enough"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    LOCATION_RADIUS_METERS: float = 10.0
    MAX_ACCURACY_METERS: float = 10.0
    MAX_FIX_AGE_SECONDS: float = 30.0
    CHALLENGE_EXPIRY_SECONDS: float = 60.0
    VISIT_GRANT_LIFETIME_MINUTES: float = 15.0

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
