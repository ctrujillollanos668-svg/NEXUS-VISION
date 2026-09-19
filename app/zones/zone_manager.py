"""
Gestor de Zonas de Seguridad para NEXUS VISION.
Permite definir, evaluar y dibujar zonas restringidas con estética táctica.
"""
from dataclasses import dataclass
from typing import List, Tuple, Dict
import cv2
import numpy as np

@dataclass
class SecurityZone:
    """Representa una zona de seguridad en coordenadas relativas (0.0 a 1.0)."""
    id: str
    name: str
    zone_type: str  # "RESTRICTED", "WARNING", "ENTRY"
    rel_coords: Tuple[float, float, float, float]
    color_normal: Tuple[int, int, int] = (0, 140, 255)  # Naranja / Ámbar
    color_alert: Tuple[int, int, int] = (0, 0, 255)     # Rojo brillante

    def get_pixel_coords(self, frame_w: int, frame_h: int) -> Tuple[int, int, int, int]:
        xmin = int(self.rel_coords[0] * frame_w)
        ymin = int(self.rel_coords[1] * frame_h)
        xmax = int(self.rel_coords[2] * frame_w)
        ymax = int(self.rel_coords[3] * frame_h)
        return xmin, ymin, xmax, ymax

    def intersects_bbox(self, bbox: Tuple[int, int, int, int], frame_w: int, frame_h: int) -> bool:
        z_xmin, z_ymin, z_max, z_ymax = self.get_pixel_coords(frame_w, frame_h)
        b_x1, b_y1, b_x2, b_y2 = bbox

        cx = (b_x1 + b_x2) // 2
        cy = (b_y1 + b_y2) // 2

        if z_xmin <= cx <= z_max and z_ymin <= cy <= z_ymax:
            return True

        return not (b_x2 < z_xmin or b_x1 > z_max or b_y2 < z_ymin or b_y1 > z_ymax)

class ZoneManager:
    """Administra las zonas configuradas y su renderizado."""

    def __init__(self):
        self.zones: Dict[str, SecurityZone] = {}
        self.enabled: bool = True
        self._load_default_zones()

    def _load_default_zones(self):
        """Carga la zona restringida por defecto (sector derecho)."""
        self.add_zone(
            SecurityZone(
                id="restricted_zone_1",
                name="ZONA RESTRINGIDA",
                zone_type="RESTRICTED",
                rel_coords=(0.55, 0.15, 0.98, 0.85),
                color_normal=(0, 100, 255),
                color_alert=(0, 0, 255)
            )
        )

    def add_zone(self, zone: SecurityZone):
        self.zones[zone.id] = zone

    def check_intrusions(self, bbox: Tuple[int, int, int, int], frame_w: int, frame_h: int) -> List[SecurityZone]:
        """Retorna la lista de zonas violadas si la vigilancia está activa."""
        if not self.enabled:
            return []
        violated_zones = []
        for zone in self.zones.values():
            if zone.intersects_bbox(bbox, frame_w, frame_h):
                violated_zones.append(zone)
        return violated_zones

    def draw_zones(self, frame: np.ndarray, active_alerts: List[str]) -> np.ndarray:
        """Dibuja las zonas de seguridad en el fotograma con estilo táctico."""
        if not self.enabled:
            return frame

        h, w, _ = frame.shape
        overlay = frame.copy()

        for zone in self.zones.values():
            xmin, ymin, xmax, ymax = zone.get_pixel_coords(w, h)
            is_active = zone.id in active_alerts

            color = zone.color_alert if is_active else zone.color_normal
            alpha = 0.32 if is_active else 0.10

            # 1. Relleno semitransparente
            cv2.rectangle(overlay, (xmin, ymin), (xmax, ymax), color, -1)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            # 2. Marco exterior y esquinas reforzadas
            border_thick = 2 if is_active else 1
            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, border_thick)

            c_len = 25
            c_thick = 3 if is_active else 2
            cv2.line(frame, (xmin, ymin), (xmin + c_len, ymin), color, c_thick)
            cv2.line(frame, (xmin, ymin), (xmin, ymin + c_len), color, c_thick)
            cv2.line(frame, (xmax, ymin), (xmax - c_len, ymin), color, c_thick)
            cv2.line(frame, (xmax, ymin), (xmax, ymin + c_len), color, c_thick)
            cv2.line(frame, (xmin, ymax), (xmin + c_len, ymax), color, c_thick)
            cv2.line(frame, (xmin, ymax), (xmin, ymax - c_len), color, c_thick)
            cv2.line(frame, (xmax, ymax), (xmax - c_len, ymax), color, c_thick)
            cv2.line(frame, (xmax, ymax), (xmax, ymax - c_len), color, c_thick)

            # 3. Etiqueta limpia sin caracteres rotos
            status_text = "[!] INTRUSION DETECTADA" if is_active else f"[{zone.name}]"
            (tw, th), _ = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            
            cv2.rectangle(frame, (xmin, ymin - th - 8), (xmin + tw + 12, ymin), color, -1)
            cv2.putText(frame, status_text, (xmin + 6, ymin - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)

        return frame
