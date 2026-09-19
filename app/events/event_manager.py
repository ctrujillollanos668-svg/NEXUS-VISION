"""
Gestor de Eventos y Capturas Inteligentes para NEXUS VISION.
Controla el intervalo de eventos (cooldown) para no duplicar fotos innecesarias
y persiste el historial en SQLite con rutas relativas a las fotos.
"""
import time
from datetime import datetime
from typing import List, Optional
import cv2
import numpy as np
from pathlib import Path

from app.database.database import SessionLocal
from app.database.models import EventLog
from app.detection.detector import Detection

class EventManager:
    """Administra la creación de eventos, almacenamiento de fotos y registro en SQLite."""

    def __init__(self, cooldown_seconds: float = 4.0, camera_id: int = 0):
        self.cooldown_seconds = cooldown_seconds
        self.camera_id = camera_id
        self.last_event_time = {}  # {object_name: last_timestamp}
        self.latest_event_msg: Optional[str] = None
        self.latest_event_time: float = 0.0

        # Ruta base de capturas: storage/snapshots
        self.snapshots_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "snapshots"

    def _save_snapshot(self, frame: np.ndarray, event_type: str) -> str:
        """Guarda una captura en storage/snapshots/YYYY/MM/DD/event_HHMMSS.jpg."""
        now = datetime.now()
        date_folder = self.snapshots_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        filename = f"{event_type.lower()}_{now.strftime('%H%M%S_%f')[:10]}.jpg"
        filepath = date_folder / filename

        cv2.imwrite(str(filepath), frame)
        return str(filepath)

    def process_detections(self, frame: np.ndarray, detections: List[Detection]) -> Optional[str]:
        """
        Evalúa las detecciones activas y genera eventos en SQLite con capturas.
        Retorna el mensaje del último evento para mostrar en el HUD si está activo.
        """
        current_time = time.time()

        for det in detections:
            # Solo generar eventos para objetos en movimiento o personas detectadas
            if not det.is_moving and det.category != "person":
                continue

            last_time = self.last_event_time.get(det.class_name_es, 0.0)

            # Verificar si ha pasado el tiempo de espera (cooldown) para este objeto
            if current_time - last_time >= self.cooldown_seconds:
                self.last_event_time[det.class_name_es] = current_time

                event_type = f"{det.class_name_en.upper().replace(' ', '_')}_DETECTADO"
                description = f"Se detectó {det.class_name_es} con confianza de {int(det.confidence * 100)}%"

                # 1. Guardar captura en disco
                snapshot_path = self._save_snapshot(frame, event_type)

                # 2. Registrar en la Base de Datos SQLite
                db = SessionLocal()
                try:
                    event = EventLog(
                        event_type=event_type,
                        object_name=det.class_name_es,
                        confidence=det.confidence,
                        camera_id=self.camera_id,
                        description=description,
                        snapshot_path=snapshot_path,
                        created_at=datetime.now()
                    )
                    db.add(event)
                    db.commit()
                    db.refresh(event)

                    self.latest_event_msg = f"📸 EVENTO #{event.id}: {det.class_name_es.upper()}"
                    self.latest_event_time = current_time
                    print(f"🚨 [EVENTO #{event.id}] {event_type} -> Guardado en BD | Captura: {snapshot_path}")

                except Exception as e:
                    print(f"❌ Error guardando evento en BD: {e}")
                    db.rollback()
                finally:
                    db.close()

        # Mantener visible la alerta en pantalla durante 2.5 segundos
        if self.latest_event_msg and (current_time - self.latest_event_time < 2.5):
            return self.latest_event_msg
        
        return None
