from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    MONGODB_URL: str = "mongodb://localhost:27017"
    ADMIN_IDS: list[int] = [702756264]
    REVIEWS_URL: str = "https://t.me/xolod"
    PORTFOLIO_URL: str = "https://t.me/xolod"


settings = Settings()
