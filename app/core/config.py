"""
Módulo de Configuración Central de NEXUS VISION.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Ruta raíz del proyecto (c:\...\python)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS VISION"
    VERSION: str = "0.3.1"
    DEBUG: bool = True
    
    # Configuración de Cámara
    CAMERA_INDEX: int = 0
    TARGET_FPS: int = 30
    
    # Configuración de IA (YOLO-World de Vocabulario Abierto Universal)
    MODEL_PATH: str = str(BASE_DIR / "models" / "yolov8s-worldv2.pt")
    CONFIDENCE_THRESHOLD: float = 0.20
    IOU_THRESHOLD: float = 0.65
    
    # Filtro de Movimiento Inteligente
    ONLY_MOVING_OBJECTS: bool = True     # Solo detectar objetos con movimiento activo
    MIN_MOTION_RATIO: float = 0.02       # Umbral mínimo de píxeles en movimiento dentro del objeto

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
