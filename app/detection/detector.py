"""
Módulo de Detección de Objetos con IA para NEXUS VISION.
Utiliza YOLOv8 para procesar fotogramas, identificar clases y categorizarlas.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple
import cv2
import numpy as np
from ultralytics import YOLO

@dataclass
class Detection:
    """Estructura de datos que representa un objeto detectado."""
    class_name: str
    category: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]          # (center_x, center_y)

class ObjectDetector:
    """Motor de inferencia de Visión Artificial."""

    # Categorización visual para agrupar objetos
    CATEGORIES: Dict[str, List[str]] = {
        "person": ["person"],
        "animal": ["dog", "cat", "bird", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"],
        "vehicle": ["car", "motorcycle", "bus", "truck", "bicycle", "airplane", "boat"],
        "device": ["cell phone", "laptop", "mouse", "remote", "keyboard", "tv"],
    }

    # Colores distintivos en formato BGR
    COLORS: Dict[str, Tuple[int, int, int]] = {
        "person": (255, 140, 0),     # Azul / Cyan brillante
        "animal": (0, 165, 255),     # Naranja
        "vehicle": (200, 0, 200),    # Púrpura / Magenta
        "device": (0, 255, 128),     # Verde Neón
        "other": (200, 200, 200)     # Gris claro
    }

    def __init__(self, model_path: str = "models/yolov8n.pt", conf_threshold: float = 0.45):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        print(f"🧠 Cargando modelo de Inteligencia Artificial ({model_path})...")
        # Carga el modelo (si no existe localmente, ultralytics lo descarga de forma segura)
        self.model = YOLO(model_path)
        print("✔️ Modelo de IA cargado y listo.")

    def _get_category(self, class_name: str) -> str:
        """Determina la categoría general a la que pertenece el objeto."""
        for cat, items in self.CATEGORIES.items():
            if class_name in items:
                return cat
        return "other"

    def detect(self, frame: np.ndarray) -> Tuple[List[Detection], Dict[str, int]]:
        """
        Ejecuta la inferencia sobre un frame y retorna la lista de detecciones y contadores.
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)[0]
        detections: List[Detection] = []
        counts: Dict[str, int] = {"person": 0, "animal": 0, "vehicle": 0, "device": 0, "other": 0}

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0].item())
            class_id = int(box.cls[0].item())
            class_name = self.model.names[class_id]

            category = self._get_category(class_name)
            counts[category] = counts.get(category, 0) + 1

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            detections.append(
                Detection(
                    class_name=class_name,
                    category=category,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y)
                )
            )

        return detections, counts

    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Dibuja bounding boxes estilizados y etiquetas en el frame."""
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = self.COLORS.get(det.category, self.COLORS["other"])

            # 1. Rectángulo principal del objeto
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 2. Esquinas reforzadas estilo HUD táctico
            line_len = max(10, min((x2 - x1) // 5, (y2 - y1) // 5))
            cv2.line(frame, (x1, y1), (x1 + line_len, y1), color, 4)
            cv2.line(frame, (x1, y1), (x1, y1 + line_len), color, 4)
            cv2.line(frame, (x2, y1), (x2 - line_len, y1), color, 4)
            cv2.line(frame, (x2, y1), (x2, y1 + line_len), color, 4)
            cv2.line(frame, (x1, y2), (x1 + line_len, y2), color, 4)
            cv2.line(frame, (x1, y2), (x1, y2 - line_len), color, 4)
            cv2.line(frame, (x2, y2), (x2 - line_len, y2), color, 4)
            cv2.line(frame, (x2, y2), (x2, y2 - line_len), color, 4)

            # 3. Etiqueta con fondo sólido
            label = f"{det.class_name.upper()} {int(det.confidence * 100)}%"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + w + 10, max(0, y1)), color, -1)
            cv2.putText(frame, label, (x1 + 5, max(0, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        return frame
