from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    # Webhook secret
    SECRET_KEY: str

    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    @property
    def database_url_asyncpg(self) -> str:
        """Асинхронный URL для подключения к базе данных."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Указываем Pydantic, что нужно читать переменные из .env файла
    model_config = SettingsConfigDict(env_file=".env")


# Создаем экземпляр настроек, который будет использоваться во всем приложении
settings = Settings()
