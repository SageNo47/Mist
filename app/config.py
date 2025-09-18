"""
application configuration
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"

    # logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # database
    database_path: str = "DATABASE_PATH"

    # user management
    # JWT
    jwt_secret_key: str = "JWT_SECRET_KEY"
    jwt_algorithm: str = "JWT_ALGORITHM"
    jwt_access_token_expire_min: int = "JWT_ACCESS_TOKEN_EXPIRE_MIN"

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()