from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "AI Executive Assistant"
    DEBUG: bool = True

    OPENAI_API_KEY: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
