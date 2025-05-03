from pydantic import BaseModel

class ConfigItem(BaseModel):
    key: str
    value: str | None

class ConfigUpdate(BaseModel):
    notion_api_key: str | None = None
    notion_database_id: str | None = None
    openrouter_api_key: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None

    class Config:
        orm_mode = True
