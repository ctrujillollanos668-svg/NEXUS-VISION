"""
Módulo de Detección de Movimiento para NEXUS VISION.
Utiliza sustracción de fondo adaptativa (MOG2) y análisis de gradiente de píxeles
para determinar con precisión qué regiones y objetos están en movimiento.
"""
from typing import Tuple
import cv2
import numpy as np

class MotionDetector:
    """Detecta movimiento general y local en fotogramas de video."""

    def __init__(self, history: int = 300, var_threshold: int = 30, detect_shadows: bool = False):
        # Subtractor adaptativo MOG2 para aislar píxeles en movimiento
        self.subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=var_threshold,
            detectShadows=detect_shadows
        )
        self.motion_mask: np.ndarray = np.array([])
        self.scene_motion_ratio: float = 0.0

    def update(self, frame: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Procesa el fotograma actual y genera la máscara binaria de movimiento.
        Retorna la máscara procesada y el porcentaje de movimiento general de la escena.
        """
        # 1. Reducir ruido con desenfoque Gaussiano leve
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)

        # 2. Obtener la máscara de movimiento
        mask = self.subtractor.apply(blurred)

        # 3. Operaciones morfológicas para rellenar huecos y eliminar ruido residual
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.dilate(mask, kernel, iterations=2)

        self.motion_mask = mask

        # 4. Calcular porcentaje de movimiento en toda la escena
        total_pixels = mask.size
        motion_pixels = cv2.countNonZero(mask)
        self.scene_motion_ratio = (motion_pixels / total_pixels) * 100.0 if total_pixels > 0 else 0.0

        return self.motion_mask, self.scene_motion_ratio

    def is_bbox_moving(self, bbox: Tuple[int, int, int, int], min_motion_ratio: float = 0.03) -> Tuple[bool, float]:
        """
        Evalúa si la región dentro de un Bounding Box tiene movimiento significativo.
        Retorna (is_moving, ratio_de_movimiento_interno).
        """
        if self.motion_mask.size == 0:
            return False, 0.0

        x1, y1, x2, y2 = bbox
        h, w = self.motion_mask.shape

        # Asegurar coordenadas dentro de los límites de la imagen
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))

        if x2 <= x1 or y2 <= y1:
            return False, 0.0

        # Extraer el recorte de la máscara de movimiento correspondiente al objeto
        bbox_mask = self.motion_mask[y1:y2, x1:x2]
        total_pixels = bbox_mask.size

        if total_pixels == 0:
            return False, 0.0

        motion_pixels = cv2.countNonZero(bbox_mask)
        motion_ratio = motion_pixels / total_pixels

        is_moving = motion_ratio >= min_motion_ratio
        return is_moving, motion_ratio
