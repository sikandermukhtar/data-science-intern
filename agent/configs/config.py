from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class AgentSettings(BaseSettings):
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    SUPERVISOR_MODEL: str = "openai/gpt-5.4"
    WORKER_MODEL: str = "openai/gpt-5.4-mini"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent # root
    SANDBOX_DIR: Path = BASE_DIR / "sandbox"
    OUTPUT_DIR: Path = BASE_DIR / "backend" / "static" 

    LANGSMITH_TRACING_V2: str = "false"
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "data-science-intern"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore" 
    )

agent_settings = AgentSettings()

agent_settings.SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
agent_settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
