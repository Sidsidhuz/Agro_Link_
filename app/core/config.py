from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE = Path(__file__).resolve().parents[2]


class DatabaseSettings(BaseModel):
    url: str = f"sqlite+aiosqlite:///{(BASE / 'data/agrolink.db').as_posix()}"
    pool_size: int = Field(default=5, ge=1)
    max_overflow: int = Field(default=5, ge=0)
    pool_timeout: float = Field(default=30, gt=0)
    pool_recycle: int = Field(default=1800, gt=0)


class AuthSettings(BaseModel):
    secret: SecretStr | None = None
    secure_cookie: bool = False
    max_age: int = Field(default=86400, gt=0)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='AGROLINK_', env_nested_delimiter='__',
        env_file=BASE / '.env', extra='ignore',
    )
    environment: Literal['development', 'test', 'production'] = 'development'
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    cors_origins: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def production_security(self):
        if self.environment == 'production':
            if not self.auth.secret or len(self.auth.secret.get_secret_value()) < 32:
                raise ValueError('Production requires an auth secret of at least 32 characters')
            if not self.auth.secure_cookie:
                raise ValueError('Production requires secure cookies')
            if '*' in self.cors_origins:
                raise ValueError('Credentialed CORS requires explicit origins')
        return self
