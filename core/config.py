from pydantic import BaseSettings

class Settings(BaseSettings):
    CACHE_DIR: str
    SAVE_DIR: str
    LOG_DIR: str
    APP_NAME: str
    COMFY_URL: str

    class Config:
        env_file = "core/config.env"