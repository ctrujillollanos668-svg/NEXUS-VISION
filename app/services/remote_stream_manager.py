"""
Módulo de Gestión de Transmisiones Remotas para NEXUS VISION.
Permite recibir y administrar transmisiones de video en vivo enviadas por múltiples dispositivos o amigos.
"""
import time
import threading
from typing import Dict, Any, List, Optional
import cv2
import numpy as np

class RemoteStreamManager:
    """Administra múltiples flujos de video entrantes desde navegadores remotos."""

    _instance: Optional['RemoteStreamManager'] = None

    @classmethod
    def get_instance(cls) -> 'RemoteStreamManager':
        if cls._instance is None:
            cls._instance = RemoteStreamManager()
        return cls._instance

    def __init__(self):
        self._streams: Dict[str, Dict[str, Any]] = {}
        self._expelled_ids: set = set()
        self._lock = threading.Lock()
        self.auto_motion_snapshot_enabled: bool = True

    def register_or_update_frame(self, stream_id: str, display_name: str, frame: np.ndarray) -> bool:
        """Actualiza el último fotograma recibido de un transmisor remoto y evalúa movimiento."""
        with self._lock:
            if stream_id in self._expelled_ids:
                return False

            now = time.time()
            if stream_id not in self._streams:
                self._streams[stream_id] = {
                    "id": stream_id,
                    "name": f"🌐 {display_name}",
                    "display_name": display_name,
                    "last_frame": frame,
                    "first_seen": now,
                    "last_update": now,
                    "type": "remote",
                    "motion_ref_gray": None,
                    "last_motion_snap_time": 0.0
                }
            else:
                self._streams[stream_id]["last_frame"] = frame
                self._streams[stream_id]["last_update"] = now

        # Detección de movimiento y captura automática
        if self.auto_motion_snapshot_enabled and frame is not None:
            self._check_motion_and_snapshot(stream_id, display_name, frame)

        return True

    def _check_motion_and_snapshot(self, stream_id: str, display_name: str, frame: np.ndarray):
        """Detecta movimiento en la cámara remota y guarda una captura automática si supera el umbral."""
        try:
            with self._lock:
                stream = self._streams.get(stream_id)
                if not stream:
                    return

                now = time.time()
                # Cooldown de 3.5 segundos entre capturas de movimiento para no saturar
                if now - stream.get("last_motion_snap_time", 0.0) < 3.5:
                    return

                # Convertir a escala de grises y reducir tamaño para cálculo ultrarrápido (< 0.5 ms)
                small = cv2.resize(frame, (160, 120))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (9, 9), 0)

                prev_gray = stream.get("motion_ref_gray")
                if prev_gray is None:
                    stream["motion_ref_gray"] = gray
                    return

                diff = cv2.absdiff(prev_gray, gray)
                _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                motion_pixels = cv2.countNonZero(thresh)
                motion_ratio = motion_pixels / (160.0 * 120.0)

                # Actualizar fotograma de referencia
                stream["motion_ref_gray"] = gray

                # Si el movimiento es significativo (> 2.5% de la escena cambió)
                if motion_ratio >= 0.025:
                    stream["last_motion_snap_time"] = now
                    # Guardar captura en hilo secundario para no retrasar el streaming
                    threading.Thread(
                        target=self._save_motion_snapshot_thread,
                        args=(stream_id, display_name, frame.copy(), motion_ratio),
                        daemon=True
                    ).start()
        except Exception as e:
            print(f"⚠️ Error en detección de movimiento remoto: {e}")

    def _save_motion_snapshot_thread(self, stream_id: str, display_name: str, frame: np.ndarray, motion_ratio: float):
        """Guarda la foto de movimiento en disco y registra el evento en la BD."""
        try:
            from datetime import datetime
            from pathlib import Path
            from app.database.database import SessionLocal
            from app.database.models import EventLog

            cam_folder = f"camara_amigo_{stream_id.replace('remote_disp_', '').replace('remote_', '')}"
            snapshots_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "snapshots"
            now = datetime.now()
            date_folder = snapshots_dir / cam_folder / now.strftime("%Y-%m-%d")
            date_folder.mkdir(parents=True, exist_ok=True)

            filename = f"movimiento_{now.strftime('%H%M%S_%f')[:10]}.jpg"
            filepath = date_folder / filename

            cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            db = SessionLocal()
            try:
                pct = int(min(1.0, motion_ratio * 4) * 100)
                event = EventLog(
                    event_type="MOTION_DETECTED",
                    object_name=f"Movimiento ({pct}%) [{display_name}]",
                    confidence=round(min(1.0, motion_ratio * 4), 2),
                    camera_id=0,
                    zone_name=f"🌐 {display_name}",
                    alert_level="WARNING",
                    description=f"Movimiento detectado automáticamente en la cámara de {display_name}",
                    snapshot_path=str(filepath),
                    created_at=now
                )
                db.add(event)
                db.commit()
                db.refresh(event)
                print(f"📸 [MOVIMIENTO DETECTADO #{event.id}] Foto guardada en '{cam_folder}': {filepath.name}")
            except Exception as e:
                db.rollback()
                print(f"❌ Error guardando evento de movimiento en BD: {e}")
            finally:
                db.close()
        except Exception as err:
            print(f"❌ Error en _save_motion_snapshot_thread: {err}")

    def is_expelled(self, stream_id: str) -> bool:
        """Verifica si el stream fue expulsado por el administrador."""
        with self._lock:
            return stream_id in self._expelled_ids

    def expel_stream(self, stream_id: str) -> bool:
        """Expulsa y revoca permanentemente el acceso a esa transmisión remota."""
        with self._lock:
            self._expelled_ids.add(stream_id)
            if stream_id in self._streams:
                del self._streams[stream_id]
            return True

    def get_frame(self, stream_id: str) -> Optional[np.ndarray]:
        """Obtiene el último fotograma de una cámara remota si está activa (< 4 seg)."""
        with self._lock:
            if stream_id in self._expelled_ids:
                return None

            stream = self._streams.get(stream_id)
            if not stream:
                return None

            if time.time() - stream["last_update"] > 4.0:
                return None

            frame = stream.get("last_frame")
            return frame.copy() if frame is not None else None

    def get_active_cameras(self) -> List[Dict[str, Any]]:
        """Retorna la lista de cámaras remotas que están transmitiendo activamente."""
        active = []
        now = time.time()
        with self._lock:
            for s_id, data in self._streams.items():
                if s_id not in self._expelled_ids and (now - data["last_update"] <= 5.0):
                    active.append({
                        "id": s_id,
                        "name": data["name"],
                        "type": "remote"
                    })
        return active

    def get_active_streams_detail(self) -> List[Dict[str, Any]]:
        """Retorna información detallada de dispositivos remotos para el panel de administración."""
        details = []
        now = time.time()
        with self._lock:
            for s_id, data in self._streams.items():
                if s_id not in self._expelled_ids and (now - data["last_update"] <= 5.0):
                    duration_secs = int(now - data.get("first_seen", now))
                    mins, secs = divmod(duration_secs, 60)
                    details.append({
                        "id": s_id,
                        "name": data["display_name"],
                        "duration": f"{mins}m {secs}s",
                        "status": "EN VIVO"
                    })
        return details

    def remove_stream(self, stream_id: str):
        with self._lock:
            if stream_id in self._streams:
                del self._streams[stream_id]
