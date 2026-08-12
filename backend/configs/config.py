from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class BackendSettings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    STATIC_DIR: Path = BASE_DIR / "backend" / "static"
    
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

backend_settings = BackendSettings()
backend_settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)