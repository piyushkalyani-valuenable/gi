"""
Simple application settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    environment: str = "development"  # development or production
    
    # Gemini AI
    gemini_api_key: str
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS (use "*" to allow all origins, or comma-separated list)
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Local Database (for development)
    local_db_host: str = "localhost"
    local_db_port: int = 3306
    local_db_user: str = "root"
    local_db_password: str = "piyupiyu"
    local_db_name: str = "mydb"
    
    # AWS (for production)
    aws_region: str = "ap-south-1"
    aws_secret_name: str = "DB_SECRET"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_local(self) -> bool:
        """Check if running locally"""
        return self.environment.lower() in ("local", "development", "dev")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


# Global settings instance
settings = Settings()
