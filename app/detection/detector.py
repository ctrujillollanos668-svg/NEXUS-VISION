"""
Módulo de Detección de Objetos Universal y Filtro de Movimiento para NEXUS VISION.
Combina YOLO-World con el detector de movimiento para ignorar objetos estáticos e inmóviles.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import cv2
import numpy as np
from ultralytics import YOLO
from app.detection.motion_detector import MotionDetector

@dataclass
class Detection:
    """Estructura de datos que representa un objeto detectado."""
    class_name_en: str
    class_name_es: str
    category: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]          # (center_x, center_y)
    area: int                        # Área para dibujo en capas
    is_moving: bool = False          # Indica si el objeto se está moviendo
    motion_ratio: float = 0.0        # Nivel de movimiento detectado

class ObjectDetector:
    """Motor de inferencia universal con soporte para filtrado de movimiento."""

    ITEMS_CATALOG: List[Tuple[str, str, str]] = [
        # Humanos y accesorios
        ("person", "Persona", "person"),
        ("glasses", "Gafas", "item"),
        ("sunglasses", "Gafas de Sol", "item"),
        ("watch", "Reloj", "device"),
        ("wristwatch", "Reloj de Mano", "device"),
        ("cap", "Gorra", "item"),
        ("hat", "Sombrero", "item"),
        ("ring", "Anillo", "item"),
        ("wallet", "Billetera", "item"),
        ("credit card", "Tarjeta", "item"),
        ("keys", "Llaves", "item"),
        ("backpack", "Mochila", "item"),

        # Útiles de escritorio, estudio y papelería
        ("pen", "Lapicero", "item"),
        ("ballpoint pen", "Lapicero", "item"),
        ("pencil", "Lapiz", "item"),
        ("notebook", "Cuaderno", "item"),
        ("book", "Libro", "item"),
        ("paper", "Papel / Hoja", "item"),
        ("scissors", "Tijeras", "item"),

        # Tecnología y cables
        ("cell phone", "Celular", "device"),
        ("smartphone", "Celular", "device"),
        ("laptop", "Computador / Laptop", "device"),
        ("computer mouse", "Mouse", "device"),
        ("keyboard", "Teclado", "device"),
        ("headphones", "Audifonos", "device"),
        ("earphones", "Auriculares", "device"),
        ("cable", "Cable", "device"),
        ("charger", "Cargador", "device"),
        ("remote control", "Control Remoto", "device"),
        ("television", "Pantalla / TV", "device"),

        # Objetos de cocina y bebidas
        ("bottle", "Botella", "item"),
        ("water bottle", "Botella", "item"),
        ("cup", "Taza / Vaso", "item"),
        ("mug", "Pocillo / Taza", "item"),
        ("glass", "Vaso", "item"),
        ("plate", "Plato", "item"),
        ("fork", "Tenedor", "item"),
        ("knife", "Cuchillo", "item"),
        ("spoon", "Cuchara", "item"),

        # Muebles y entorno
        ("chair", "Silla", "furniture"),
        ("table", "Mesa", "furniture"),
        ("desk", "Escritorio", "furniture"),
        ("bed", "Cama", "furniture"),
        ("door", "Puerta", "furniture"),
        ("potted plant", "Planta", "furniture"),

        # Animales y vehículos
        ("dog", "Perro", "animal"),
        ("cat", "Gato", "animal"),
        ("bird", "Ave", "animal"),
        ("car", "Auto", "vehicle"),
        ("motorcycle", "Motocicleta", "vehicle"),
        ("bicycle", "Bicicleta", "vehicle")
    ]

    COLORS: Dict[str, Tuple[int, int, int]] = {
        "person": (255, 140, 0),      # Azul / Cyan
        "animal": (0, 165, 255),      # Naranja
        "vehicle": (200, 0, 200),     # Púrpura
        "device": (0, 255, 128),      # Verde Neón
        "furniture": (255, 200, 0),   # Amarillo Oro
        "item": (0, 220, 255),        # Amarillo Neón
        "other": (200, 200, 200)      # Gris claro
    }

    def __init__(self, model_path: str = "models/yolov8s-worldv2.pt", conf_threshold: float = 0.20, iou_threshold: float = 0.65):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        print(f"🧠 Cargando modelo de Inteligencia Artificial ({model_path})...")
        self.model = YOLO(model_path)

        self.english_classes = [item[0] for item in self.ITEMS_CATALOG]
        self.es_map = {item[0]: item[1] for item in self.ITEMS_CATALOG}
        self.category_map = {item[0]: item[2] for item in self.ITEMS_CATALOG}

        try:
            self.model.set_classes(self.english_classes)
            print(f"✔️ {len(self.english_classes)} clases universales con soporte de movimiento activo.")
        except Exception as e:
            print(f"⚠️ Nota de inicialización: {e}")

    def detect(
        self,
        frame: np.ndarray,
        motion_detector: Optional[MotionDetector] = None,
        only_moving: bool = True,
        min_motion_ratio: float = 0.02
    ) -> Tuple[List[Detection], Dict[str, int], Dict[str, int]]:
        """
        Ejecuta la inferencia y aplica el filtro de movimiento si only_moving es True.
        """
        results = self.model(
            frame,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            agnostic_nms=False,
            verbose=False
        )[0]

        detections: List[Detection] = []
        category_counts: Dict[str, int] = {"person": 0, "animal": 0, "vehicle": 0, "device": 0, "furniture": 0, "item": 0, "other": 0}
        item_inventory: Dict[str, int] = {}

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0].item())
            class_id = int(box.cls[0].item())
            class_name_en = results.names.get(class_id, "unknown")
            class_name_es = self.es_map.get(class_name_en, class_name_en.capitalize())
            category = self.category_map.get(class_name_en, "other")

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            area = (x2 - x1) * (y2 - y1)

            # Evaluar si el objeto se está moviendo usando el motion detector
            is_moving = True
            motion_ratio = 1.0

            if motion_detector is not None:
                is_moving, motion_ratio = motion_detector.is_bbox_moving((x1, y1, x2, y2), min_motion_ratio=min_motion_ratio)
                
                # Si el modo "solo en movimiento" está activo y el objeto está completamente quieto, lo ignoramos
                if only_moving and not is_moving:
                    continue

            category_counts[category] = category_counts.get(category, 0) + 1
            item_inventory[class_name_es] = item_inventory.get(class_name_es, 0) + 1

            detections.append(
                Detection(
                    class_name_en=class_name_en,
                    class_name_es=class_name_es,
                    category=category,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y),
                    area=area,
                    is_moving=is_moving,
                    motion_ratio=motion_ratio
                )
            )

        # Ordenar por área para dibujo en capas
        detections.sort(key=lambda d: d.area, reverse=True)

        return detections, category_counts, item_inventory

    def draw_detections(self, frame: np.ndarray, detections: List[Detection], only_moving: bool = True) -> np.ndarray:
        """Dibuja bounding boxes estilizados con indicador visual de movimiento."""
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = self.COLORS.get(det.category, self.COLORS["other"])

            is_person = (det.category == "person")
            border_thickness = 1 if is_person else 2

            # 1. Rectángulo principal
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, border_thickness)

            # 2. Esquinas reforzadas
            line_len = max(6, min((x2 - x1) // 5, (y2 - y1) // 5, 20))
            corner_thick = 2 if is_person else 3
            cv2.line(frame, (x1, y1), (x1 + line_len, y1), color, corner_thick)
            cv2.line(frame, (x1, y1), (x1, y1 + line_len), color, corner_thick)
            cv2.line(frame, (x2, y1), (x2 - line_len, y1), color, corner_thick)
            cv2.line(frame, (x2, y1), (x2, y1 + line_len), color, corner_thick)
            cv2.line(frame, (x1, y2), (x1 + line_len, y2), color, corner_thick)
            cv2.line(frame, (x1, y2), (x1, y2 - line_len), color, corner_thick)
            cv2.line(frame, (x2, y2), (x2 - line_len, y2), color, corner_thick)
            cv2.line(frame, (x2, y2), (x2 - line_len, y2), color, corner_thick)

            # 3. Etiqueta con indicador de movimiento
            motion_tag = " [MOV]" if det.is_moving else ""
            label = f"{det.class_name_es.upper()}{motion_tag} {int(det.confidence * 100)}%"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            
            label_y = max(h + 6, y1)
            cv2.rectangle(frame, (x1, label_y - h - 6), (x1 + w + 8, label_y), color, -1)
            cv2.putText(frame, label, (x1 + 4, label_y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

        return frame
