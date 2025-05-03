from pydantic import BaseModel

class NotionConfig(BaseModel):
    notion_api_key: str | None = None
    notion_database_id: str | None = None

    class Config:
        orm_mode = True

class OpenRouterConfig(BaseModel):
    openrouter_api_key: str | None = None

    class Config:
        orm_mode = True

class TelegramConfig(BaseModel):
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    class Config:
        orm_mode = True

class ConfigUpdate(BaseModel):
    notion: NotionConfig | None = None
    openrouter: OpenRouterConfig | None = None
    telegram: TelegramConfig | None = None
