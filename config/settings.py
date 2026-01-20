# ==========================================
# File: config/settings.py
# ==========================================
import os
import yaml
from pathlib import Path
from typing import Literal, Any, Dict, Tuple, Type
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict, 
    PydanticBaseSettingsSource,
)

# --- Define Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_YAML_PATH = BASE_DIR / "config" / "config.yml"

class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A custom settings source that loads configuration from a YAML file.
    """
    def get_field_value(self, field: Any, field_name: str) -> Tuple[Any, str, bool]:
        # Not used directly, but required by abstract base class in some versions
        return None, field_name, False

    def __call__(self) -> Dict[str, Any]:
        """
        Load the yaml file and return a dictionary of settings.
        """
        if not CONFIG_YAML_PATH.exists():
            return {}
        
        try:
            with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return config_data or {}
        except Exception as e:
            # In production, you might want to log this warning
            print(f"WARNING: Could not load config.yml: {e}")
            return {}

class Settings(BaseSettings):
    """
    Centralized Configuration.
    Hierarchy: Env Vars > .env file > config.yml > Defaults
    """

    # --- App Info ---
    APP_NAME: str = "VendorMasterAI"
    ENV: Literal["development", "production"] = "development"

    # --- LLM Configuration ---
    LLM_PROVIDER: Literal["openai", "gemini"] = "openai"
    OPENAI_MODEL_NAME: str = "gpt-4o"
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    EMBEDDING_MODEL_NAME: str = "text-embedding-3-small"
    
    # --- API Keys (Secrets - Prefer .env) ---
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # --- Database & Storage Paths ---
    # These can be overridden in config.yml, but defaults are calculated here
    SQL_DB_NAME: str = "vendor_master.db"
    VECTOR_STORE_DIR_NAME: str = "chroma_db"
    
    # --- Business Logic Thresholds ---
    MAX_RETRIES: int = 3
    SIMILARITY_THRESHOLD: float = 0.60

    # --- Computed Properties (Not loadable from Config) ---
    @property
    def SQL_DB_PATH(self) -> str:
        return str(BASE_DIR / "data" / "sql" / self.SQL_DB_NAME)

    @property
    def VECTOR_STORE_PATH(self) -> str:
        return str(BASE_DIR / "data" / "vector_store" / self.VECTOR_STORE_DIR_NAME)

    @property
    def RAW_DATA_DIR(self) -> Path:
        return BASE_DIR / "data" / "raw"

    @property
    def BASE_DIR(self) -> Path:
        return BASE_DIR

    # --- Pydantic Configuration ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra keys in config.yml/env that aren't defined here
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """
        Define the priority order for loading settings.
        1. Init arguments (runtime)
        2. Environment variables (os.environ)
        3. .env file
        4. config.yml (Custom Source)
        5. Defaults
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

# Singleton Instance
settings = Settings()

# Validation Hook
if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
    raise ValueError("LLM_PROVIDER is 'openai' but OPENAI_API_KEY is missing.")
if settings.LLM_PROVIDER == "gemini" and not settings.GOOGLE_API_KEY:
    raise ValueError("LLM_PROVIDER is 'gemini' but GOOGLE_API_KEY is missing.")