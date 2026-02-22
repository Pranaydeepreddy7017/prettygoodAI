import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    
    MODEL_NAME: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    TEST_LINE: str = os.getenv("TEST_LINE", "")
    PUBLIC_BASE_URL: str = os.environ["PUBLIC_BASE_URL"]

    TWILIO_ACCOUNT_SID: str = os.environ["TWILIO_ACCOUNT_SID"]
    TWILIO_AUTH_TOKEN: str = os.environ["TWILIO_AUTH_TOKEN"]
    TWILIO_FROM_NUMBER: str = os.environ["TWILIO_FROM_NUMBER"]

    MAX_TURNS: int = int(os.getenv("MAX_TURNS", "8"))

settings = Settings()
