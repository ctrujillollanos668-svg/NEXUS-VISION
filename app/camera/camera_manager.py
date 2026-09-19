"""
Módulo de Gestión de Cámara para NEXUS VISION.
Controla la captura de video, cálculo de FPS, HUD superior con estado de movimiento y barra de inventario.
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

    def draw_hud(
        self,
        frame: np.ndarray,
        category_counts: Optional[Dict[str, int]] = None,
        inventory: Optional[Dict[str, int]] = None,
        only_moving: bool = True,
        scene_motion: float = 0.0
    ) -> np.ndarray:
        """Dibuja el panel de control con estado de movimiento e inventario dinámico."""
        h, w, _ = frame.shape
        category_counts = category_counts or {"person": 0, "animal": 0, "vehicle": 0, "device": 0}
        inventory = inventory or {}

        overlay = frame.copy()

        # 1. Panel Superior Izquierdo (Estado del Sistema y Filtro de Movimiento)
        cv2.rectangle(overlay, (10, 10), (370, 90), (18, 18, 18), -1)
        
        # 2. Panel Superior Derecho (Contador Rápido)
        cv2.rectangle(overlay, (w - 360, 10), (w - 10, 100), (18, 18, 18), -1)

        # 3. Barra Inferior de Inventario
        cv2.rectangle(overlay, (10, h - 50), (w - 10, h - 10), (15, 15, 15), -1)
        
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

        # Bordes decorativos
        motion_border_color = (0, 255, 128) if only_moving else (0, 180, 255)
        cv2.rectangle(frame, (10, 10), (370, 90), motion_border_color, 1)
        cv2.rectangle(frame, (w - 360, 10), (w - 10, 100), (0, 180, 255), 1)
        cv2.rectangle(frame, (10, h - 50), (w - 10, h - 10), (255, 180, 0), 1)

        # Textos Panel Izquierdo
        status_mode = "[FILTRO: SOLO MOVIMIENTO]" if only_moving else "[MODO: TODOS LOS OBJETOS]"
        cv2.putText(frame, f"NEXUS VISION | {status_mode}", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.46, (0, 255, 180), 2)
        cv2.putText(frame, f"FPS: {self.fps:.1f} | Movimiento Sala: {scene_motion:.1f}%", (20, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1)
        cv2.putText(frame, "Presiona 'm' para alternar filtro | 'q' salir", (20, 74),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1)

        # Textos Panel Derecho
        cv2.putText(frame, "RESUMEN EN MOVIMIENTO" if only_moving else "RESUMEN TOTAL", (w - 345, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 255), 1)
        cv2.putText(frame, f"Personas:    {category_counts.get('person', 0)}", (w - 345, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 140, 0), 1)
        cv2.putText(frame, f"Dispositivos: {category_counts.get('device', 0)}", (w - 345, 66),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 128), 1)
        cv2.putText(frame, f"Utiles/Objetos: {category_counts.get('item', 0)}", (w - 345, 84),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)

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
        """Libera la cámara y ventanas."""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        print("🛑 Cámara detenida y recursos liberados.")
