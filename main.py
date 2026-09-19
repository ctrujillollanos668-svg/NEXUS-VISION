"""
NEXUS VISION — Sistema de Cámara Inteligente con IA
Detección universal de objetos, traducción al español e inventario en tiempo real.
"""
import os
import cv2
from app.core.config import settings
from app.camera.camera_manager import CameraManager
from app.detection.detector import ObjectDetector

def main():
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} — v{settings.VERSION}")
    print("=" * 60)

    # Crear carpeta models si no existe
    os.makedirs("models", exist_ok=True)

    # 1. Iniciar Detector de Inteligencia Artificial con 80 clases en Español
    detector = ObjectDetector(
        model_path=settings.MODEL_PATH,
        conf_threshold=settings.CONFIDENCE_THRESHOLD
    )

    # 2. Iniciar Administrador de Cámara
    cam = CameraManager(
        camera_index=settings.CAMERA_INDEX,
        target_fps=settings.TARGET_FPS
    )

    if not cam.start():
        return

    print("📺 Transmisión con IA Universal iniciada.")
    print("💡 Muestra cualquier objeto cotidiano (celular, botella, taza, libro, tijeras, etc.)")

    try:
        while cam.is_running:
            success, frame = cam.read_frame()
            if not success:
                break

            # 3. Detectar objetos, categorías e inventario exacto en español
            detections, category_counts, inventory = detector.detect(frame)

            # 4. Dibujar Bounding Boxes y etiquetas en español
            frame = detector.draw_detections(frame, detections)

            # 5. Dibujar HUD y barra inferior con inventario
            frame = cam.draw_hud(frame, category_counts, inventory)

            # 6. Mostrar el resultado en pantalla
            cv2.imshow(f"{settings.PROJECT_NAME} - Reconocimiento Universal IA", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        print("\nDetención solicitada...")
    finally:
        cam.stop()

if __name__ == "__main__":
    main()
