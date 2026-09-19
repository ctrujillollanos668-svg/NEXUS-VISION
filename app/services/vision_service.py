"""
Servicio Central de Visión Artificial en Tiempo Real para NEXUS VISION.
"""
import time
import threading
from typing import Optional, Dict, Any
import cv2

from app.core.config import settings
from app.camera.camera_manager import CameraManager
from app.detection.detector import ObjectDetector
from app.detection.motion_detector import MotionDetector
from app.zones.zone_manager import ZoneManager
from app.alerts.alert_manager import AlertManager
from app.services.remote_stream_manager import RemoteStreamManager

class VisionService:
    """Motor de procesamiento continuo de video con IA y streaming web."""

    _instance: Optional['VisionService'] = None

    @classmethod
    def get_instance(cls) -> 'VisionService':
        if cls._instance is None:
            cls._instance = VisionService()
        return cls._instance

    def __init__(self):
        self.detector = ObjectDetector(
            model_path=settings.MODEL_PATH,
            conf_threshold=settings.CONFIDENCE_THRESHOLD,
            iou_threshold=settings.IOU_THRESHOLD
        )
        self.motion_detector = MotionDetector()
        self.zone_manager = ZoneManager()
        self.remote_stream_manager = RemoteStreamManager.get_instance()
        self.alert_manager = AlertManager(
            cooldown_seconds=settings.ALERT_COOLDOWN_SECONDS,
            enable_sound=settings.ENABLE_ALERT_SOUND,
            camera_id=settings.CAMERA_INDEX
        )
        self.cam = CameraManager(
            camera_index=settings.CAMERA_INDEX,
            target_fps=settings.TARGET_FPS
        )

        self.only_moving = settings.ONLY_MOVING_OBJECTS
        self.auto_snapshot_enabled = True
        self.last_auto_snapshot_time = 0.0
        self.auto_snapshot_cooldown = 8.0
        self.is_running = False
        self.render_thread: Optional[threading.Thread] = None
        self.ai_thread: Optional[threading.Thread] = None

        self._latest_jpeg: Optional[bytes] = None
        self._raw_frame: Optional[Any] = None
        self._lock = threading.Lock()
        self._data_lock = threading.Lock()

        # Estado de IA en memoria compartida
        self._cached_detections = []
        self._cached_category_counts: Dict[str, int] = {}
        self._cached_inventory: Dict[str, int] = {}
        self._cached_active_zones = []
        self._cached_alert_banner: Optional[str] = None
        self._cached_scene_motion: float = 0.0

        # Métricas para el Dashboard
        self.current_fps: float = 0.0
        self.current_inference_ms: float = 0.0
        self.current_scene_motion: float = 0.0
        self.current_category_counts: Dict[str, int] = {}
        self.current_inventory: Dict[str, int] = {}
        self.current_alert_banner: Optional[str] = None
        self.total_detections_session: int = 0

    def start(self):
        """Inicia la cámara, el hilo de streaming a 30 FPS y el hilo de IA en segundo plano."""
        if self.is_running:
            return

        if not self.cam.start():
            print("⚠️ Error iniciando la cámara en VisionService.")
            return

        self.is_running = True
        
        # 1. Hilo de IA en segundo plano (Inferencia continua sin bloquear video)
        self.ai_thread = threading.Thread(target=self._ai_worker_loop, daemon=True)
        self.ai_thread.start()

        # 2. Hilo de Renderizado y Streaming en Vivo (30 FPS fluidos)
        self.render_thread = threading.Thread(target=self._render_stream_loop, daemon=True)
        self.render_thread.start()
        
        print("🚀 VisionService: Streaming a 30 FPS + Inferencia de IA en hilos independientes.")

    def _ai_worker_loop(self):
        """Hilo de inferencia de IA en segundo plano."""
        while self.is_running:
            frame_to_process = None
            with self._lock:
                if self._raw_frame is not None:
                    frame_to_process = self._raw_frame.copy()

            if frame_to_process is None:
                time.sleep(0.01)
                continue

            # 1. Mapa de movimiento
            _, scene_motion = self.motion_detector.update(frame_to_process)

            # 2. Inferencia de IA optimizada
            detections, category_counts, inventory = self.detector.detect(
                frame=frame_to_process,
                motion_detector=self.motion_detector,
                only_moving=self.only_moving,
                min_motion_ratio=settings.MIN_MOTION_RATIO
            )

            # 3. Reglas y Alertas
            active_zones, alert_banner = self.alert_manager.evaluate_rules(
                frame=frame_to_process,
                detections=detections,
                zone_manager=self.zone_manager
            )

            # 4. Captura Automática Inteligente (si está activa y hay personas/dispositivos)
            current_t = time.time()
            if self.auto_snapshot_enabled and detections:
                if current_t - self.last_auto_snapshot_time >= self.auto_snapshot_cooldown:
                    # Priorizar personas o primer objeto
                    target_det = next((d for d in detections if d.category in ["person", "device"]), detections[0])
                    if target_det and target_det.confidence >= 0.40:
                        self.last_auto_snapshot_time = current_t
                        threading.Thread(
                            target=self.take_snapshot,
                            args=(f"Detección Automática: {target_det.class_name_es} ({int(target_det.confidence*100)}%)", target_det.class_name_es),
                            daemon=True
                        ).start()

            # 5. Actualizar estado compartido
            with self._data_lock:
                self._cached_detections = detections
                self._cached_category_counts = category_counts
                self._cached_inventory = inventory
                self._cached_active_zones = active_zones
                self._cached_alert_banner = alert_banner
                self._cached_scene_motion = scene_motion
                self.current_inference_ms = self.detector.last_inference_ms
                self.total_detections_session += len(detections)

            # Pequeña pausa para no saturar el 100% de los núcleos de la CPU
            time.sleep(0.035)

    def _render_stream_loop(self):
        """Bucle de renderizado táctico y streaming web a 30 FPS constantes."""
        failed_reads = 0
        while self.is_running:
            current_cam_str = str(self.cam.camera_index)
            is_remote = current_cam_str.startswith("remote_")

            if is_remote:
                frame = self.remote_stream_manager.get_frame(current_cam_str)
                success = (frame is not None)
            else:
                success, frame = self.cam.read_frame()

            if not success or frame is None:
                failed_reads += 1
                if not is_remote and failed_reads > 30 and failed_reads % 50 == 0:
                    print("⚠️ Intentando reconectar cámara...")
                    self.cam.start()

                # Generar fotograma de espera
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                title_msg = "ESPERANDO TRANSMISION DE CAMARA REMOTA..." if is_remote else "NEXUS VISION - ESPERANDO SENAL DE CAMARA"
                cv2.putText(placeholder, title_msg, (40, 220),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 180), 2)
                cv2.putText(placeholder, f"Canal activo: {current_cam_str} | Selecciona otra camara si no hay transmision", (40, 260),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1)
                
                ret, buffer = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret:
                    with self._lock:
                        self._latest_jpeg = buffer.tobytes()
                time.sleep(0.05)
                continue

            failed_reads = 0

            # Guardar fotograma crudo para el hilo de IA
            with self._lock:
                self._raw_frame = frame

            # Obtener últimas detecciones disponibles
            with self._data_lock:
                detections = list(self._cached_detections)
                category_counts = dict(self._cached_category_counts)
                inventory = dict(self._cached_inventory)
                active_zones = list(self._cached_active_zones)
                alert_banner = self._cached_alert_banner
                scene_motion = self._cached_scene_motion

            # Dibujar capas visuales
            display_frame = frame.copy()
            display_frame = self.zone_manager.draw_zones(display_frame, active_alerts=active_zones)
            display_frame = self.detector.draw_detections(display_frame, detections, only_moving=self.only_moving)
            display_frame = self.cam.draw_hud(
                frame=display_frame,
                category_counts=category_counts,
                inventory=inventory,
                only_moving=self.only_moving,
                scene_motion=scene_motion,
                event_alert=alert_banner
            )

            # Codificar a JPEG para streaming Web
            ret, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                with self._lock:
                    self._latest_jpeg = buffer.tobytes()
                    self.current_fps = self.cam.fps
                    self.current_scene_motion = scene_motion
                    self.current_category_counts = category_counts
                    self.current_inventory = inventory
                    self.current_alert_banner = alert_banner

            time.sleep(0.001)

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": "ONLINE" if self.is_running else "OFFLINE",
                "fps": round(self.current_fps, 1),
                "inference_ms": round(self.current_inference_ms, 1),
                "device_name": self.detector.device_name,
                "scene_motion": round(self.current_scene_motion, 1),
                "only_moving": self.only_moving,
                "auto_snapshot": self.auto_snapshot_enabled,
                "sound_enabled": self.alert_manager.enable_sound,
                "zones_enabled": self.zone_manager.enabled,
                "categories": self.current_category_counts,
                "inventory": self.current_inventory,
                "total_items_in_scene": sum(self.current_inventory.values()),
                "active_alert": self.current_alert_banner,
                "camera_index": self.cam.camera_index,
                "project_name": settings.PROJECT_NAME,
                "version": settings.VERSION
            }

    def list_cameras(self) -> Dict[str, Any]:
        """Lista las cámaras locales y remotas conectadas al sistema."""
        local_cams = CameraManager.list_available_cameras(active_index=self.cam.camera_index)
        remote_cams = self.remote_stream_manager.get_active_cameras()

        all_cams = list(local_cams) + list(remote_cams)

        current_in_list = any(str(c["id"]) == str(self.cam.camera_index) for c in all_cams)
        if not current_in_list:
            all_cams.insert(0, {
                "id": self.cam.camera_index,
                "name": f"📷 Cámara #{self.cam.camera_index} (Activa)",
                "type": "custom"
            })
        return {
            "current_camera": self.cam.camera_index,
            "cameras": all_cams
        }

    def switch_camera(self, new_camera: Any) -> bool:
        """Cambia la cámara activa de forma segura (soporta locales y remotas)."""
        new_cam_str = str(new_camera)
        with self._lock:
            if new_cam_str.startswith("remote_"):
                self.cam.stop()
                self.cam.camera_index = new_cam_str
                print(f"✔️ Conectado a cámara remota: {new_cam_str}")
                return True
            else:
                success = self.cam.switch_source(new_camera)
                if success:
                    self.alert_manager.camera_id = int(new_camera) if str(new_camera).isdigit() else 0
                return success

    def toggle_motion(self) -> bool:
        self.only_moving = not self.only_moving
        return self.only_moving

    def toggle_auto_snapshot(self) -> bool:
        self.auto_snapshot_enabled = not self.auto_snapshot_enabled
        return self.auto_snapshot_enabled

    def toggle_sound(self) -> bool:
        self.alert_manager.enable_sound = not self.alert_manager.enable_sound
        return self.alert_manager.enable_sound

    def toggle_zones(self) -> bool:
        self.zone_manager.enabled = not self.zone_manager.enabled
        return self.zone_manager.enabled

    def take_snapshot(self, description: str = "Captura Manual", object_name: str = "Foto Manual") -> Optional[Dict[str, Any]]:
        """Toma una foto instantánea en alta resolución y la registra en la base de datos."""
        with self._lock:
            if self._raw_frame is None:
                return None
            frame = self._raw_frame.copy()

        from datetime import datetime
        from pathlib import Path
        from app.database.database import SessionLocal
        from app.database.models import EventLog

        snapshots_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "snapshots"
        now = datetime.now()
        date_folder = snapshots_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        filename = f"manual_{now.strftime('%H%M%S_%f')[:10]}.jpg"
        filepath = date_folder / filename

        cv2.imwrite(str(filepath), frame)
        web_url = f"/snapshots/{now.strftime('%Y')}/{now.strftime('%m')}/{now.strftime('%d')}/{filename}"

        db = SessionLocal()
        try:
            event = EventLog(
                event_type="MANUAL_SNAPSHOT",
                object_name=object_name,
                confidence=1.0,
                camera_id=self.cam.camera_index if isinstance(self.cam.camera_index, int) or str(self.cam.camera_index).isdigit() else 0,
                zone_name="Control Manual",
                alert_level="INFO",
                description=description,
                snapshot_path=str(filepath),
                created_at=now
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            print(f"📸 [FOTO MANUAL #{event.id}] Captura guardada con éxito en: {filepath}")
            return {
                "id": event.id,
                "snapshot_url": web_url,
                "time": now.strftime("%H:%M:%S"),
                "date": now.strftime("%Y-%m-%d"),
                "description": description
            }
        except Exception as e:
            print(f"❌ Error guardando captura manual en BD: {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def stop(self):
        self.is_running = False
        if self.cam:
            self.cam.stop()
        print("🛑 VisionService detenido.")
