import fastapi
import uvicorn
import requests
from api.server import app
import os
from core.config import Settings
env = Settings()



if __name__ == "__main__":
    os.makedirs(env.CACHE_DIR, exist_ok=True)
    os.makedirs(env.SAVE_DIR, exist_ok=True)
    os.makedirs(env.LOG_DIR, exist_ok=True)
    uvicorn.run(app,
                host="0.0.0.0",
                port=8000)