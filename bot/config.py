from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./beautybot.db"
    ADMIN_IDS: list[int] = [702756264]
    REVIEWS_URL: str = "https://t.me/xolod"
    PORTFOLIO_URL: str = "https://t.me/xolod"


settings = Settings()
