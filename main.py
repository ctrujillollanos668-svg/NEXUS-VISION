"""
NEXUS VISION — Sistema de Cámara Inteligente con IA
Fase 3 & 4: Inferencia en tiempo real, Bounding Boxes y Contadores.
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

    # 1. Iniciar Detector de Inteligencia Artificial
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

    print("📺 Transmisión con IA iniciada. Muestra objetos o colócate frente a la cámara.")

    try:
        while cam.is_running:
            success, frame = cam.read_frame()
            if not success:
                break

            # 3. Detectar objetos con la IA
            detections, counts = detector.detect(frame)

            # 4. Dibujar Bounding Boxes en los objetos detectados
            frame = detector.draw_detections(frame, detections)

            # 5. Dibujar HUD con FPS y Contadores
            frame = cam.draw_hud(frame, counts)

            # 6. Mostrar el resultado en pantalla
            cv2.imshow(f"{settings.PROJECT_NAME} - IA en Tiempo Real", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        print("\nDetención solicitada...")
    finally:
        cam.stop()

if __name__ == "__main__":
    main()
