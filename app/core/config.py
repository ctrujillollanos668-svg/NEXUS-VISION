"""
Módulo de Configuración Central de NEXUS VISION.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Ruta raíz del proyecto (c:\...\python)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS VISION"
    VERSION: str = "0.2.1"
    DEBUG: bool = True
    
    # Configuración de Cámara
    CAMERA_INDEX: int = 0
    TARGET_FPS: int = 30
    
    # Configuración de IA (Umbral optimizado al 35% para detectar más objetos cotidianos)
    MODEL_PATH: str = str(BASE_DIR / "models" / "yolov8n.pt")
    CONFIDENCE_THRESHOLD: float = 0.35

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
