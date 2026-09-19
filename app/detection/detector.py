"""
Módulo de Detección de Objetos con IA para NEXUS VISION.
Utiliza YOLOv8 para procesar fotogramas, identificar 80 clases de objetos y traducirlas al español.
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple
import cv2
import numpy as np
from ultralytics import YOLO

@dataclass
class Detection:
    """Estructura de datos que representa un objeto detectado."""
    class_name_en: str
    class_name_es: str
    category: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]          # (center_x, center_y)

class ObjectDetector:
    """Motor de inferencia y traducción de Visión Artificial."""

    # Traducción completa de las 80 clases COCO de YOLO al Español
    COCO_SPANISH_MAP: Dict[str, str] = {
        "person": "Persona",
        "bicycle": "Bicicleta",
        "car": "Auto",
        "motorcycle": "Motocicleta",
        "airplane": "Avion",
        "bus": "Autobus",
        "train": "Tren",
        "truck": "Camion",
        "boat": "Barco",
        "traffic light": "Semaforo",
        "fire hydrant": "Hidrante",
        "stop sign": "Senal Stop",
        "parking meter": "Parquimetro",
        "bench": "Banco",
        "bird": "Ave",
        "cat": "Gato",
        "dog": "Perro",
        "horse": "Caballo",
        "sheep": "Oveja",
        "cow": "Vaca",
        "elephant": "Elefante",
        "bear": "Oso",
        "zebra": "Cebra",
        "giraffe": "Jirafa",
        "backpack": "Mochila",
        "umbrella": "Paraguas",
        "handbag": "Bolso",
        "tie": "Corbata",
        "suitcase": "Maleta",
        "frisbee": "Frisbee",
        "skis": "Esquis",
        "snowboard": "Snowboard",
        "sports ball": "Pelota",
        "kite": "Cometa",
        "baseball bat": "Bate",
        "baseball glove": "Guante",
        "skateboard": "Patineta",
        "surfboard": "Tabla Surf",
        "tennis racket": "Raqueta",
        "bottle": "Botella",
        "wine glass": "Copa",
        "cup": "Taza / Vaso",
        "fork": "Tenedor",
        "knife": "Cuchillo",
        "spoon": "Cuchara",
        "bowl": "Plato / Tazon",
        "banana": "Platano",
        "apple": "Manzana",
        "sandwich": "Sandwich",
        "orange": "Naranja",
        "broccoli": "Brocoli",
        "carrot": "Zanahoria",
        "hot dog": "Perro Caliente",
        "pizza": "Pizza",
        "donut": "Dona",
        "cake": "Pastel",
        "chair": "Silla",
        "couch": "Sofa",
        "potted plant": "Planta",
        "bed": "Cama",
        "dining table": "Mesa",
        "toilet": "Inodoro",
        "tv": "Pantalla / TV",
        "laptop": "Computador / Laptop",
        "mouse": "Mouse / Raton",
        "remote": "Control Remoto",
        "keyboard": "Teclado",
        "cell phone": "Celular",
        "microwave": "Microondas",
        "oven": "Horno",
        "toaster": "Tostadora",
        "sink": "Fregadero",
        "refrigerator": "Nevera",
        "book": "Libro / Cuaderno",
        "clock": "Reloj",
        "vase": "Florero",
        "scissors": "Tijeras",
        "teddy bear": "Peluche",
        "hair drier": "Secador",
        "toothbrush": "Cepillo de Dientes"
    }

    # Categorización general para métricas
    CATEGORIES: Dict[str, List[str]] = {
        "person": ["person"],
        "animal": ["dog", "cat", "bird", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe"],
        "vehicle": ["car", "motorcycle", "bus", "truck", "bicycle", "airplane", "boat"],
        "device": ["cell phone", "laptop", "mouse", "remote", "keyboard", "tv", "microwave", "oven", "toaster", "clock"],
        "furniture": ["chair", "couch", "bed", "dining table", "potted plant"],
        "item": ["bottle", "cup", "book", "backpack", "handbag", "umbrella", "scissors", "toothbrush", "fork", "knife", "spoon", "bowl"]
    }

    # Colores por categoría (BGR)
    COLORS: Dict[str, Tuple[int, int, int]] = {
        "person": (255, 140, 0),      # Azul / Cyan
        "animal": (0, 165, 255),      # Naranja
        "vehicle": (200, 0, 200),     # Púrpura
        "device": (0, 255, 128),      # Verde Neón
        "furniture": (255, 200, 0),   # Amarillo Oro
        "item": (0, 220, 255),        # Amarillo brillante
        "other": (200, 200, 200)      # Gris claro
    }

    def __init__(self, model_path: str = "models/yolov8n.pt", conf_threshold: float = 0.35):
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        print(f"🧠 Cargando modelo de Inteligencia Artificial ({model_path})...")
        self.model = YOLO(model_path)
        print("✔️ Modelo de IA cargado y listo para detección universal.")

    def _get_category(self, class_name: str) -> str:
        """Determina la categoría general a la que pertenece el objeto."""
        for cat, items in self.CATEGORIES.items():
            if class_name in items:
                return cat
        return "other"

    def detect(self, frame: np.ndarray) -> Tuple[List[Detection], Dict[str, int], Dict[str, int]]:
        """
        Ejecuta la inferencia sobre un frame y retorna:
        - Lista de detecciones individuales
        - Conteo general por categoría
        - Inventario exacto por nombre en español (ej: {"Celular": 1, "Taza / Vaso": 2})
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)[0]
        detections: List[Detection] = []
        category_counts: Dict[str, int] = {"person": 0, "animal": 0, "vehicle": 0, "device": 0, "furniture": 0, "item": 0, "other": 0}
        item_inventory: Dict[str, int] = {}

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0].item())
            class_id = int(box.cls[0].item())
            class_name_en = self.model.names[class_id]
            class_name_es = self.COCO_SPANISH_MAP.get(class_name_en, class_name_en.capitalize())

            category = self._get_category(class_name_en)
            category_counts[category] = category_counts.get(category, 0) + 1
            item_inventory[class_name_es] = item_inventory.get(class_name_es, 0) + 1

            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            detections.append(
                Detection(
                    class_name_en=class_name_en,
                    class_name_es=class_name_es,
                    category=category,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=(center_x, center_y)
                )
            )

        return detections, category_counts, item_inventory

    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Dibuja bounding boxes estilizados y etiquetas en español."""
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = self.COLORS.get(det.category, self.COLORS["other"])

            # 1. Rectángulo principal del objeto
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # 2. Esquinas reforzadas estilo HUD táctico
            line_len = max(8, min((x2 - x1) // 5, (y2 - y1) // 5))
            cv2.line(frame, (x1, y1), (x1 + line_len, y1), color, 3)
            cv2.line(frame, (x1, y1), (x1, y1 + line_len), color, 3)
            cv2.line(frame, (x2, y1), (x2 - line_len, y1), color, 3)
            cv2.line(frame, (x2, y1), (x2, y1 + line_len), color, 3)
            cv2.line(frame, (x1, y2), (x1 + line_len, y2), color, 3)
            cv2.line(frame, (x1, y2), (x1, y2 - line_len), color, 3)
            cv2.line(frame, (x2, y2), (x2 - line_len, y2), color, 3)
            cv2.line(frame, (x2, y2), (x2, y2 - line_len), color, 3)

            # 3. Etiqueta en español con fondo sólido
            label = f"{det.class_name_es.upper()} {int(det.confidence * 100)}%"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - 22)), (x1 + w + 8, max(0, y1)), color, -1)
            cv2.putText(frame, label, (x1 + 4, max(0, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 1, cv2.LINE_AA)

        return frame
