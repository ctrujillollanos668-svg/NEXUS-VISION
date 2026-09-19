"""
Módulo de Configuración Central de NEXUS VISION.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Ruta raíz del proyecto (c:\...\python)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXUS VISION"
    VERSION: str = "0.4.0"
    DEBUG: bool = True
    
    # Configuración de Cámara
    CAMERA_INDEX: int = 0
    TARGET_FPS: int = 30
    
    # Configuración de IA
    MODEL_PATH: str = str(BASE_DIR / "models" / "yolov8s-worldv2.pt")
    CONFIDENCE_THRESHOLD: float = 0.20
    IOU_THRESHOLD: float = 0.65
    
    # Filtro de Movimiento
    ONLY_MOVING_OBJECTS: bool = True
    MIN_MOTION_RATIO: float = 0.02
    
    # Configuración de Zonas de Seguridad y Alertas
    ENABLE_ALERT_SOUND: bool = True        # Emitir sonido de alerta en Windows
    ALERT_COOLDOWN_SECONDS: float = 15.0   # Intervalo espaciado entre capturas de alerta (15 segs)
    SNAPSHOT_ONLY_ON_ALERT: bool = True    # Tomar fotos solo cuando haya alerta en zona restringida

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
