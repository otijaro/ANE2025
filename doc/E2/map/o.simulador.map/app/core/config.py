import os
from pydantic import BaseModel

class Settings(BaseModel):
    DB_PATH: str = os.getenv("OSIM_DB", "osim.db")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

settings = Settings()
