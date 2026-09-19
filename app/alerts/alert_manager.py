"""
Gestor de Alertas y Reglas de Seguridad para NEXUS VISION.
Emite alertas sonoras, anuncios de voz hablados en Windows, capturas y registros en SQLite.
"""
import time
import threading
from datetime import datetime
from typing import List, Tuple, Optional, Set
import cv2
import numpy as np
from pathlib import Path

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from app.database.database import SessionLocal
from app.database.models import EventLog
from app.detection.detector import Detection
from app.zones.zone_manager import ZoneManager
from app.voice.voice_engine import VoiceEngine

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
        """Emite un sonido táctico de alarma en segundo plano."""
        if not self.enable_sound or not HAS_WINSOUND:
            return

        def _sound_worker():
            try:
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

        clean_name = object_name.lower().replace(' ', '_').replace('/', '_')
        filename = f"alerta_{clean_name}_{now.strftime('%H%M%S_%f')[:10]}.jpg"
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
        """
        current_time = time.time()
        h, w, _ = frame.shape
        active_zone_ids: Set[str] = set()

        for det in detections:
            violated_zones = zone_manager.check_intrusions(det.bbox, w, h)

            for zone in violated_zones:
                active_zone_ids.add(zone.id)

                if current_time - self.last_alert_time >= self.cooldown_seconds:
                    self.last_alert_time = current_time
                    event_type = f"INTRUSION_{zone.name.replace(' ', '_').upper()}"
                    description = f"Alerta de seguridad: {det.class_name_es} detectado dentro de {zone.name}"
                    
                    self.active_alert_banner = f"🚨 ALERTA: {det.class_name_es.upper()} EN {zone.name}"
                    self.banner_expire_time = current_time + 4.0

                    # Despachar foto, sonido y registro en segundo plano sin congelar la cámara
                    snapshot_frame = frame.copy()
                    zone_name = zone.name
                    obj_name = det.class_name_es
                    conf = det.confidence

                    def _async_alert_handler():
                        self._play_alarm_sound()
                        try:
                            snapshot_path = self._save_alert_snapshot(snapshot_frame, zone_name, obj_name)
                            db = SessionLocal()
                            try:
                                event = EventLog(
                                    event_type=event_type,
                                    object_name=obj_name,
                                    confidence=conf,
                                    camera_id=self.camera_id,
                                    zone_name=zone_name,
                                    alert_level="ALERT",
                                    description=description,
                                    snapshot_path=snapshot_path,
                                    created_at=datetime.now()
                                )
                                db.add(event)
                                db.commit()
                                db.refresh(event)
                                print(f"🚨 [ALERTA #{event.id}] {obj_name} en {zone_name} -> Captura: {snapshot_path}")
                            except Exception as db_err:
                                print(f"❌ Error guardando alerta en BD: {db_err}")
                                db.rollback()
                            finally:
                                db.close()
                        except Exception as e:
                            print(f"❌ Error procesando alerta: {e}")

                    threading.Thread(target=_async_alert_handler, daemon=True).start()

        banner_text = None
        if self.active_alert_banner and current_time < self.banner_expire_time:
            banner_text = self.active_alert_banner

        return list(active_zone_ids), banner_text
