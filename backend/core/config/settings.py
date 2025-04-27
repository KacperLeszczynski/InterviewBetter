from pydantic import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = "key"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()