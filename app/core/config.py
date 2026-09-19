"""
Módulo de Configuración Central de NEXUS VISION.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS VISION"
    VERSION: str = "0.5.2"
    DEBUG: bool = True
    
    # Servidor Web
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Cámara e Inferencia
    CAMERA_INDEX: int = 0
    TARGET_FPS: int = 30
    MODEL_PATH: str = str(BASE_DIR / "models" / "yolov8s-worldv2.pt")
    CONFIDENCE_THRESHOLD: float = 0.20
    IOU_THRESHOLD: float = 0.65
    
    # Filtro de Movimiento
    ONLY_MOVING_OBJECTS: bool = True
    MIN_MOTION_RATIO: float = 0.02
    
    # Zonas y Alertas
    ENABLE_ALERT_SOUND: bool = True
    ALERT_COOLDOWN_SECONDS: float = 15.0
    
    # IA Generativa Real (Google Gemini Multimodal)
    GEMINI_API_KEY: str = ""
    AI_MODEL_NAME: str = "gemini-3.6-flash"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
