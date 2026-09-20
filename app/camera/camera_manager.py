"""
Módulo de Gestión de Cámara para NEXUS VISION.
Controla la captura de video, cálculo de FPS, HUD táctico, alertas rojas de intrusión, barra de inventario
y soporte para escaneo y cambio dinámico de múltiples cámaras / fuentes de video.
"""
import os
import time
import threading
from typing import Optional, Tuple, Dict, List, Any, Union

# Silenciar avisos internos y advertencias C++ de OpenCV (Obsensor, FFMPEG)
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

import cv2
import numpy as np

try:
    cv2.setLogLevel(0)
except Exception:
    pass

class CameraManager:
    """Administra la captura de video, escaneo de dispositivos y la interfaz HUD."""

    _cached_hardware_cams: Optional[List[Dict[str, Any]]] = None

    def __init__(self, camera_index: Union[int, str] = 0, target_fps: int = 30):
        self.camera_index = camera_index
        self.raw_source: str = str(camera_index)
        self.target_fps = target_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.prev_time = 0.0
        self.fps = 0.0
        self._lock = threading.Lock()

    @classmethod
    def list_available_cameras(cls, max_tested: int = 3, active_index: Optional[Union[int, str]] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Detecta webcams conectadas. Cachea el resultado para no sondear puertos vacíos repetidamente
        evitando advertencias DSHOW en la consola.
        """
        active_int = int(active_index) if active_index is not None and str(active_index).isdigit() else None

        if cls._cached_hardware_cams is None or force_refresh:
            found = []
            for index in range(max_tested):
                temp_cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if temp_cap.isOpened():
                    ret, frame = temp_cap.read()
                    if ret and frame is not None:
                        mean_lum = float(frame.mean())
                        label = f"📷 Cámara #{index} (Sensor IR Infrarrojo)" if mean_lum < 1.5 else f"📷 Cámara #{index} (Webcam RGB Color)"
                        found.append({"id": index, "name": label, "type": "hardware"})
                    temp_cap.release()

            if not found:
                found.append({"id": 0, "name": "📷 Cámara #0 (Webcam Principal)", "type": "hardware"})
            cls._cached_hardware_cams = found

        cams = []
        for c in cls._cached_hardware_cams:
            item = dict(c)
            if active_int is not None and item["id"] == active_int:
                item["name"] = f"📷 Cámara #{item['id']} (En Uso)"
            cams.append(item)
        return cams

    def start(self) -> bool:
        """Inicia la captura de video con fallback automático de backends (DirectShow -> Default)."""
        with self._lock:
            print(f"📷 Conectando a la fuente de video ({self.camera_index})...")
            
            # Liberar si ya existía
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

            # Si es un índice numérico en Windows
            if isinstance(self.camera_index, int) or (isinstance(self.camera_index, str) and self.camera_index.isdigit()):
                cam_idx = int(self.camera_index)
                # 1. Intentar DirectShow
                self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    # 2. Fallback a backend por defecto (MSMF en Windows)
                    self.cap = cv2.VideoCapture(cam_idx)
            else:
                # Si es URL RTSP / HTTP o ruta de archivo de video
                self.cap = cv2.VideoCapture(str(self.raw_source or self.camera_index))
            
            if not self.cap or not self.cap.isOpened():
                print(f"❌ Error: No se pudo acceder a la fuente {self.camera_index}.")
                self.is_running = False
                return False

            # Validar que la fuente remota o archivo entregue fotogramas reales
            if isinstance(self.camera_index, str):
                ret, test_frame = self.cap.read()
                if not ret or test_frame is None or test_frame.size == 0:
                    print(f"❌ Error: La fuente {self.camera_index} no entrega fotogramas de video válidos.")
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None
                    self.is_running = False
                    return False
                # Rebobinar videos locales al inicio
                try:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                except Exception:
                    pass

            # Configuración de resolución y buffer
            try:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            self.prev_time = time.time()
            print(f"✔️ Fuente de video {self.camera_index} iniciada a 640x480.")
            return True

    def switch_source(self, new_source: Union[int, str], raw_path: Optional[str] = None) -> bool:
        """
        Cambia en caliente la fuente de video actual por una nueva sin colapsar el sistema.
        Si la nueva fuente falla, revierte de forma automática a la cámara anterior.
        """
        old_index = self.camera_index
        old_raw = self.raw_source
        print(f"🔄 Cambiando fuente de video de {self.camera_index} -> {new_source}...")
        self.stop()
        self.camera_index = int(new_source) if str(new_source).isdigit() else new_source
        self.raw_source = str(raw_path or new_source)
        success = self.start()
        if not success:
            print(f"⚠️ Error al abrir {new_source}. Revirtiendo de forma segura a {old_index}...")
            self.camera_index = old_index
            self.raw_source = old_raw
            self.start()
            return False
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Lee el siguiente frame de forma segura y actualiza FPS con rebobinado infinito."""
        with self._lock:
            if not self.is_running or self.cap is None:
                return False, None

            # Rebobinado preventivo continuo para archivos de video (.mp4, .avi)
            try:
                total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if total_frames and total_frames > 0:
                    pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                    if pos >= total_frames - 2:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            except Exception:
                pass

            ret, frame = self.cap.read()
            if not ret or frame is None:
                # Rebobinar y reintentar si se alcanzó el fin del video
                try:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                except Exception:
                    pass

                if not ret or frame is None:
                    return False, None

            current_time = time.time()
            diff = current_time - self.prev_time
            if diff > 0:
                instant_fps = 1.0 / diff
                if self.fps <= 0.5:
                    self.fps = instant_fps
                else:
                    self.fps = 0.85 * self.fps + 0.15 * instant_fps
            self.prev_time = current_time

            return True, frame

    def draw_hud(
        self,
        frame: np.ndarray,
        category_counts: Optional[Dict[str, int]] = None,
        inventory: Optional[Dict[str, int]] = None,
        only_moving: bool = True,
        scene_motion: float = 0.0,
        event_alert: Optional[str] = None
    ) -> np.ndarray:
        """Dibuja el panel de control, alertas de intrusión e inventario."""
        h, w, _ = frame.shape
        category_counts = category_counts or {"person": 0, "animal": 0, "vehicle": 0, "device": 0}
        inventory = inventory or {}

        overlay = frame.copy()

        # 1. Panel Superior Izquierdo (Estado del Sistema y Filtro de Movimiento)
        cv2.rectangle(overlay, (10, 10), (380, 90), (18, 18, 18), -1)
        
        # 2. Panel Superior Derecho (Contador Rápido)
        cv2.rectangle(overlay, (w - 360, 10), (w - 10, 100), (18, 18, 18), -1)

        # 3. Barra Inferior de Inventario
        cv2.rectangle(overlay, (10, h - 50), (w - 10, h - 10), (15, 15, 15), -1)
        
        # 4. Banner Central de Alerta de Intrusión (Rojo Táctico)
        if event_alert:
            banner_w = 460
            cv2.rectangle(overlay, (w // 2 - (banner_w // 2), 12), (w // 2 + (banner_w // 2), 62), (0, 0, 180), -1)

        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

        # Bordes decorativos
        motion_border_color = (0, 255, 128) if only_moving else (0, 180, 255)
        cv2.rectangle(frame, (10, 10), (380, 90), motion_border_color, 1)
        cv2.rectangle(frame, (w - 360, 10), (w - 10, 100), (0, 180, 255), 1)
        cv2.rectangle(frame, (10, h - 50), (w - 10, h - 10), (255, 180, 0), 1)

        # Banner de alerta visual
        if event_alert:
            banner_w = 460
            bx1, bx2 = w // 2 - (banner_w // 2), w // 2 + (banner_w // 2)
            cv2.rectangle(frame, (bx1, 12), (bx2, 62), (0, 50, 255), 2)
            cv2.putText(frame, event_alert, (bx1 + 15, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)

        # Textos Panel Izquierdo
        cam_tag = f"CAM #{self.camera_index}" if isinstance(self.camera_index, int) or str(self.camera_index).isdigit() else "CAM IP/STREAM"
        status_mode = "[FILTRO: SOLO MOVIMIENTO]" if only_moving else "[MODO: TODOS LOS OBJETOS]"
        cv2.putText(frame, f"NEXUS VISION | {cam_tag} | {status_mode}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 180), 2)
        cv2.putText(frame, f"FPS: {self.fps:.1f} | Movimiento Sala: {scene_motion:.1f}%", (20, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1)
        cv2.putText(frame, "Presiona 'm' para alternar filtro | 'q' salir", (20, 74),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)

        # Textos Panel Derecho
        cv2.putText(frame, "RESUMEN EN MOVIMIENTO" if only_moving else "RESUMEN TOTAL", (w - 345, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)
        total_people = category_counts.get('person', 0) + category_counts.get('face', 0)
        cv2.putText(frame, f"Personas/Caras:  {total_people}", (w - 345, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 140, 0), 1)
        cv2.putText(frame, f"Animales/Perros: {category_counts.get('animal', 0)}", (w - 345, 66),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
        cv2.putText(frame, f"Dispositivos:    {category_counts.get('device', 0)}", (w - 345, 84),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1)

        # Textos Barra Inferior
        if inventory:
            items_str = " | ".join([f"{name} ({qty})" for name, qty in inventory.items()])
            tag = "EN MOVIMIENTO" if only_moving else "EN ESCENA"
            inventory_text = f"📋 {tag} ({sum(inventory.values())} obj): {items_str}"
        else:
            tag = "en movimiento" if only_moving else "en la escena"
            inventory_text = f"📋 Esperando objetos {tag}..."

        if len(inventory_text) > 85:
            inventory_text = inventory_text[:82] + "..."

        cv2.putText(frame, inventory_text, (25, h - 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (255, 255, 255), 1, cv2.LINE_AA)

        return frame

    def stop(self):
        """Libera la cámara."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        print("🛑 Cámara detenida y recursos liberados.")

