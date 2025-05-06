from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_DIR = ".local"
DATABASE_URL = f"sqlite:///{LOCAL_DIR}/flashcards.db"

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".env.prod"), extra="ignore")

app_config = AppConfig()
