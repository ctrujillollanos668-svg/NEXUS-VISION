"""
Gestor de Alertas y Reglas de Seguridad para NEXUS VISION.
Controla el sonido de advertencia en Windows en segundo plano (sin congelar la cámara),
el guardado de fotos espaciadas y el registro en la base de datos SQLite.
"""
import os
import time
import threading
from datetime import datetime
from typing import List, Tuple, Optional, Set
import cv2
import numpy as np
from pathlib import Path

# Módulo de sonido nativo en Windows
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from app.database.database import SessionLocal
from app.database.models import EventLog
from app.detection.detector import Detection
from app.zones.zone_manager import ZoneManager, SecurityZone

class AlertManager:
    """Motor de evaluación de reglas de seguridad y despacho de alertas."""

    def __init__(
        self,
        cooldown_seconds: float = 15.0,
        enable_sound: bool = True,
        camera_id: int = 0
    ):
        self.cooldown_seconds = cooldown_seconds
        self.enable_sound = enable_sound
        self.camera_id = camera_id

        self.last_alert_time: float = 0.0
        self.active_alert_banner: Optional[str] = None
        self.banner_expire_time: float = 0.0

        # Directorio de fotos
        self.snapshots_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "snapshots"

    def _play_alarm_sound(self):
        """Emite un sonido de alarma en segundo plano para no congelar la cámara."""
        if not self.enable_sound or not HAS_WINSOUND:
            return

        def _sound_worker():
            try:
                # Dos pitidos tácticos de advertencia (frecuencia 1600Hz y 1900Hz)
                winsound.Beep(1600, 150)
                time.sleep(0.05)
                winsound.Beep(1900, 200)
            except Exception:
                pass

        threading.Thread(target=_sound_worker, daemon=True).start()

    def _save_alert_snapshot(self, frame: np.ndarray, zone_name: str, object_name: str) -> str:
        """Guarda la foto de la intrusión en storage/snapshots/YYYY/MM/DD/."""
        now = datetime.now()
        date_folder = self.snapshots_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        filename = f"alerta_{object_name.lower()}_{now.strftime('%H%M%S_%f')[:10]}.jpg"
        filepath = date_folder / filename

        cv2.imwrite(str(filepath), frame)
        return str(filepath)

    def evaluate_rules(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        zone_manager: ZoneManager
    ) -> Tuple[List[str], Optional[str]]:
        """
        Evalúa si algún objeto o persona viola una zona de seguridad.
        Retorna:
        - Lista de IDs de zonas con alerta activa
        - Texto del banner de alerta para la interfaz
        """
        current_time = time.time()
        h, w, _ = frame.shape
        active_zone_ids: Set[str] = set()

        for det in detections:
            # Comprobar si este objeto intersecta alguna zona
            violated_zones = zone_manager.check_intrusions(det.bbox, w, h)

            for zone in violated_zones:
                active_zone_ids.add(zone.id)

                # Comprobar si ha pasado el tiempo espaciado (cooldown) para disparar la alerta completa
                if current_time - self.last_alert_time >= self.cooldown_seconds:
                    self.last_alert_time = current_time

                    event_type = f"INTRUSION_{zone.name.replace(' ', '_').upper()}"
                    description = f"Alerta de seguridad: {det.class_name_es} detectado dentro de {zone.name}"

                    # 1. Reproducir sonido de alarma
                    self._play_alarm_sound()

                    # 2. Guardar captura fotográfica de la intrusión
                    snapshot_path = self._save_alert_snapshot(frame, zone.name, det.class_name_es)

                    # 3. Registrar Alerta Crítica en SQLite
                    db = SessionLocal()
                    try:
                        event = EventLog(
                            event_type=event_type,
                            object_name=det.class_name_es,
                            confidence=det.confidence,
                            camera_id=self.camera_id,
                            zone_name=zone.name,
                            alert_level="ALERT",
                            description=description,
                            snapshot_path=snapshot_path,
                            created_at=datetime.now()
                        )
                        db.add(event)
                        db.commit()
                        db.refresh(event)

                        self.active_alert_banner = f"🚨 ALERTA #{event.id}: {det.class_name_es.upper()} EN {zone.name}"
                        self.banner_expire_time = current_time + 4.0
                        print(f"🚨 [ALERTA DE SEGURIDAD #{event.id}] {det.class_name_es} en {zone.name} -> Captura: {snapshot_path}")

                    except Exception as e:
                        print(f"❌ Error guardando alerta en BD: {e}")
                        db.rollback()
                    finally:
                        db.close()

        # Mantener visible el banner de advertencia si no ha expirado
        banner_text = None
        if self.active_alert_banner and current_time < self.banner_expire_time:
            banner_text = self.active_alert_banner

        return list(active_zone_ids), banner_text
