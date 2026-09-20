"""
Módulo de Gestión de Cámaras IP y Streams RTSP para NEXUS VISION.
Permite registrar, almacenar de forma persistente y probar cámaras de seguridad reales (CCTV, RTSP, ONVIF).
"""
import os
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import cv2

# Forzar transporte TCP en OpenCV FFmpeg para evitar pérdida de paquetes en RTSP
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

STORAGE_FILE = Path(__file__).resolve().parent.parent.parent / "storage" / "ip_cameras.json"

class IPCameraManager:
    """Gestiona el catálogo persistente de cámaras IP y de seguridad RTSP."""

    _instance: Optional['IPCameraManager'] = None

    @classmethod
    def get_instance(cls) -> 'IPCameraManager':
        if cls._instance is None:
            cls._instance = IPCameraManager()
        return cls._instance

    def __init__(self):
        self._cameras: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        """Carga las cámaras guardadas desde el archivo JSON de configuración."""
        try:
            STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
            if STORAGE_FILE.exists():
                with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                    self._cameras = json.load(f)
            else:
                self._cameras = []
                self._save()
        except Exception as e:
            print(f"⚠️ Error cargando cámaras IP desde {STORAGE_FILE}: {e}")
            self._cameras = []

    def _save(self):
        """Guarda la lista de cámaras en el archivo JSON."""
        try:
            with open(STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cameras, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error guardando cámaras IP en {STORAGE_FILE}: {e}")

    def get_cameras(self) -> List[Dict[str, Any]]:
        """Retorna la lista de todas las cámaras IP configuradas."""
        with self._lock:
            return list(self._cameras)

    @staticmethod
    def get_preset_public_cameras() -> List[Dict[str, Any]]:
        """Retorna cámaras de seguridad públicas y demostración de circuito cerrado."""
        base_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "videos"
        video_traffic = base_dir / "cctv_traffic.mp4"
        video_pedestrians = base_dir / "cctv_pedestrians.mp4"
        return [
            {
                "id": "pub_cctv_traffic",
                "name": "🚗 Cámara CCTV Tráfico Urbano (Garantizada 24/7)",
                "location": "Avenida Metropolitana (Demostración CCTV)",
                "url": str(video_traffic),
                "desc": "Feed continuo de circuito cerrado. IA detectando vehículos, autos y movimiento sin cortes.",
                "tag": "Garantizada 100%"
            },
            {
                "id": "pub_cctv_pedestrians",
                "name": "🚶 Cámara CCTV Peatonal y Seguridad (Garantizada 24/7)",
                "location": "Paso Peatonal y Vigilancia Perimetral",
                "url": str(video_pedestrians),
                "desc": "Circuito cerrado en vivo. IA analizando personas, bicicletas y peatones en tiempo real.",
                "tag": "Garantizada 100%"
            }
        ]

    def add_camera(self, name: str, url: str) -> Dict[str, Any]:
        """Registra una nueva cámara IP / RTSP y la persiste."""
        with self._lock:
            # Generar ID único
            cam_id = f"ip_cam_{int(time.time() * 1000) % 1000000}"
            clean_name = name.strip() or f"Cámara IP #{len(self._cameras) + 1}"
            new_cam = {
                "id": cam_id,
                "name": f"🛡️ {clean_name}",
                "display_name": clean_name,
                "url": url.strip(),
                "type": "ip_camera",
                "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self._cameras.append(new_cam)
            self._save()
            return new_cam

    def remove_camera(self, camera_id: str) -> bool:
        """Elimina una cámara IP del catálogo."""
        with self._lock:
            initial_count = len(self._cameras)
            self._cameras = [c for c in self._cameras if c.get("id") != camera_id]
            if len(self._cameras) < initial_count:
                self._save()
                return True
            return False

    def test_connection(self, url: str, timeout_seconds: float = 6.0) -> Tuple[bool, str]:
        """
        Prueba si la URL RTSP o HTTP responde y devuelve al menos un fotograma válido.
        Usa un hilo con límite de tiempo para no congelar la aplicación si la IP no responde.
        """
        result = {"success": False, "message": "Tiempo de espera agotado al conectar con la cámara."}

        def _worker():
            try:
                cap = cv2.VideoCapture(url.strip())
                if not cap.isOpened():
                    result["message"] = "No se pudo abrir la URL del stream. Verifica la dirección IP, usuario y contraseña."
                    return
                
                # Intentar leer un frame de prueba
                ret, frame = cap.read()
                cap.release()

                if ret and frame is not None and frame.size > 0:
                    h, w = frame.shape[:2]
                    result["success"] = True
                    result["message"] = f"Conexión exitosa. Señal de video recibida ({w}x{h})."
                else:
                    result["message"] = "La cámara respondió pero no entregó ningún fotograma de video."
            except Exception as e:
                result["message"] = f"Error conectando a la cámara: {str(e)}"

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            return False, "Tiempo de espera agotado (Timeout). Verifica que la cámara esté encendida y en la misma red."

        return result["success"], result["message"]
