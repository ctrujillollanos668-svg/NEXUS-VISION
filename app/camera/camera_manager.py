"""
Módulo de Gestión de Cámara para NEXUS VISION.
"""
import time
from typing import Optional, Tuple, Dict
import cv2
import numpy as np

class CameraManager:
    """Administra la captura de video y la interfaz HUD."""

    def __init__(self, camera_index: int = 0, target_fps: int = 30):
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.prev_time = 0.0
        self.fps = 0.0

    def start(self) -> bool:
        """Inicia la captura de video desde la cámara."""
        print(f"📷 Conectando a la cámara (Índice {self.camera_index})...")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            print(f"❌ Error: No se pudo acceder a la cámara {self.camera_index}.")
            self.is_running = False
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.is_running = True
        self.prev_time = time.time()
        print(f"✔️ Cámara {self.camera_index} lista.")
        return True

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Lee el siguiente frame y actualiza FPS."""
        if not self.is_running or self.cap is None:
            return False, None

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return False, None

        current_time = time.time()
        diff = current_time - self.prev_time
        if diff > 0:
            self.fps = 1.0 / diff
        self.prev_time = current_time

        return True, frame

    def draw_hud(self, frame: np.ndarray, counts: Optional[Dict[str, int]] = None) -> np.ndarray:
        """Dibuja el panel de control superior y contadores de IA en tiempo real."""
        h, w, _ = frame.shape
        counts = counts or {"person": 0, "animal": 0, "vehicle": 0, "device": 0, "other": 0}

        # 1. Panel superior izquierdo (Estado y FPS)
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (330, 85), (20, 20, 20), -1)
        # 2. Panel superior derecho (Contadores de Objetos)
        cv2.rectangle(overlay, (w - 360, 10), (w - 10, 105), (20, 20, 20), -1)
        
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Bordes decorativos
        cv2.rectangle(frame, (10, 10), (330, 85), (0, 220, 100), 1)
        cv2.rectangle(frame, (w - 360, 10), (w - 10, 105), (0, 180, 255), 1)

        # Texto HUD izquierdo
        cv2.putText(frame, "NEXUS VISION | IA ACTIVA", (20, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 180), 2)
        cv2.putText(frame, f"FPS: {self.fps:.1f} | Cam: {self.camera_index} ({w}x{h})", (20, 54),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(frame, "Presiona 'q' o 'ESC' para salir", (20, 74),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)

        # Texto HUD derecho (Contadores)
        cv2.putText(frame, "OBJETOS DETECTADOS EN VIVO", (w - 345, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)
        cv2.putText(frame, f"Personas:     {counts['person']}", (w - 345, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 140, 0), 1)
        cv2.putText(frame, f"Dispositivos: {counts['device']}", (w - 345, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1)
        cv2.putText(frame, f"Animales: {counts['animal']} | Autos: {counts['vehicle']}", (w - 345, 88),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        return frame

    def stop(self):
        """Libera la cámara y ventanas."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        print("🛑 Cámara detenida y recursos liberados.")
