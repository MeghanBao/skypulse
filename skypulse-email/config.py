"""
SkyPulse 2.0 - Configuration Module
Loads environment variables and provides configuration settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""
    
    # Email IMAP (Receiving)
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
    IMAP_EMAIL = os.getenv("IMAP_EMAIL")
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
    
    # Email SMTP (Sending)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL = os.getenv("SMTP_EMAIL")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    # Subscription
    SUBSCRIBE_EMAIL = os.getenv("SUBSCRIBE_EMAIL", "subscribe@skypulse.com")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skypulse.db")
    
    # AI/LLM
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
    
    # Scheduler
    CHECK_EMAIL_INTERVAL_MINUTES = int(os.getenv("CHECK_EMAIL_INTERVAL_MINUTES", "30"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            "IMAP_EMAIL",
            "IMAP_PASSWORD",
            "SMTP_EMAIL",
            "SMTP_PASSWORD",
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")


# Validate on import
Config.validate()
