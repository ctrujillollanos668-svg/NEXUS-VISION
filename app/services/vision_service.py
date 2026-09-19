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
        self.is_running = False
        self.thread: Optional[threading.Thread] = None

        self._latest_jpeg: Optional[bytes] = None
        self._lock = threading.Lock()

        # Métricas para el Dashboard
        self.current_fps: float = 0.0
        self.current_inference_ms: float = 0.0
        self.current_scene_motion: float = 0.0
        self.current_category_counts: Dict[str, int] = {}
        self.current_inventory: Dict[str, int] = {}
        self.current_alert_banner: Optional[str] = None
        self.total_detections_session: int = 0

    def start(self):
        """Inicia la cámara y el hilo de procesamiento de IA."""
        if self.is_running:
            return

        if not self.cam.start():
            print("⚠️ Error iniciando la cámara en VisionService.")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        print("🚀 VisionService: Pipeline de IA iniciado en segundo plano para la Web.")

    def _process_loop(self):
        """Bucle continuo de inferencia y codificación de streaming."""
        while self.is_running:
            success, frame = self.cam.read_frame()
            if not success or frame is None:
                time.sleep(0.01)
                continue

            # 1. Mapa de movimiento
            _, scene_motion = self.motion_detector.update(frame)

            # 2. Inferencia de IA
            detections, category_counts, inventory = self.detector.detect(
                frame=frame,
                motion_detector=self.motion_detector,
                only_moving=self.only_moving,
                min_motion_ratio=settings.MIN_MOTION_RATIO
            )

            # 3. Reglas y Alertas
            active_zones, alert_banner = self.alert_manager.evaluate_rules(
                frame=frame,
                detections=detections,
                zone_manager=self.zone_manager
            )

            # 4. Dibujar capas tácticas
            frame = self.zone_manager.draw_zones(frame, active_alerts=active_zones)
            frame = self.detector.draw_detections(frame, detections, only_moving=self.only_moving)
            frame = self.cam.draw_hud(
                frame=frame,
                category_counts=category_counts,
                inventory=inventory,
                only_moving=self.only_moving,
                scene_motion=scene_motion,
                event_alert=alert_banner
            )

            # 5. Codificar a JPEG para streaming Web
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                with self._lock:
                    self._latest_jpeg = buffer.tobytes()
                    self.current_fps = self.cam.fps
                    self.current_inference_ms = self.detector.last_inference_ms
                    self.current_scene_motion = scene_motion
                    self.current_category_counts = category_counts
                    self.current_inventory = inventory
                    self.current_alert_banner = alert_banner
                    self.total_detections_session += len(detections)

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
        """Lista las cámaras disponibles en el sistema y la activa."""
        available = CameraManager.list_available_cameras()
        # Asegurar que al menos la cámara actual aparezca si no fue detectada por el escáner rápido
        current_in_list = any(c["id"] == self.cam.camera_index for c in available)
        if not current_in_list:
            available.insert(0, {
                "id": self.cam.camera_index,
                "name": f"📷 Cámara Actual ({self.cam.camera_index})",
                "type": "custom"
            })
        return {
            "current_camera": self.cam.camera_index,
            "cameras": available
        }

    def switch_camera(self, new_camera: Any) -> bool:
        """Cambia la cámara activa de forma segura."""
        with self._lock:
            success = self.cam.switch_source(new_camera)
            if success:
                self.alert_manager.camera_id = int(new_camera) if str(new_camera).isdigit() else 0
            return success

    def toggle_motion(self) -> bool:
        self.only_moving = not self.only_moving
        return self.only_moving

    def toggle_sound(self) -> bool:
        self.alert_manager.enable_sound = not self.alert_manager.enable_sound
        return self.alert_manager.enable_sound

    def toggle_zones(self) -> bool:
        self.zone_manager.enabled = not self.zone_manager.enabled
        return self.zone_manager.enabled

    def stop(self):
        self.is_running = False
        if self.cam:
            self.cam.stop()
        print("🛑 VisionService detenido.")
