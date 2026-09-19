"""
NEXUS VISION — Sistema de Cámara Inteligente con IA
Detección Universal con Filtro de Movimiento Inteligente.
"""
import os
import cv2
from app.core.config import settings
from app.camera.camera_manager import CameraManager
from app.detection.detector import ObjectDetector
from app.detection.motion_detector import MotionDetector

def main():
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} — v{settings.VERSION}")
    print("=" * 60)

    # Crear carpeta models si no existe
    os.makedirs("models", exist_ok=True)

    # 1. Iniciar Detector de Inteligencia Artificial Universal
    detector = ObjectDetector(
        model_path=settings.MODEL_PATH,
        conf_threshold=settings.CONFIDENCE_THRESHOLD,
        iou_threshold=settings.IOU_THRESHOLD
    )

    # 2. Iniciar Detector de Movimiento
    motion_detector = MotionDetector()

    # 3. Iniciar Administrador de Cámara
    cam = CameraManager(
        camera_index=settings.CAMERA_INDEX,
        target_fps=settings.TARGET_FPS
    )

    if not cam.start():
        return

    only_moving_mode = settings.ONLY_MOVING_OBJECTS

    print("📺 Transmisión con IA y Filtro de Movimiento iniciada.")
    print("💡 Atajos de teclado:")
    print("   - 'm': Alternar entre 'Solo Objetos en Movimiento' y 'Todos los Objetos'")
    print("   - 'q' o ESC: Salir")

    try:
        while cam.is_running:
            success, frame = cam.read_frame()
            if not success:
                break

            # 4. Actualizar mapa de movimiento
            _, scene_motion = motion_detector.update(frame)

            # 5. Detectar objetos filtrando según movimiento
            detections, category_counts, inventory = detector.detect(
                frame=frame,
                motion_detector=motion_detector,
                only_moving=only_moving_mode,
                min_motion_ratio=settings.MIN_MOTION_RATIO
            )

            # 6. Dibujar Bounding Boxes
            frame = detector.draw_detections(frame, detections, only_moving=only_moving_mode)

            # 7. Dibujar HUD y barra inferior
            frame = cam.draw_hud(
                frame=frame,
                category_counts=category_counts,
                inventory=inventory,
                only_moving=only_moving_mode,
                scene_motion=scene_motion
            )

            # 8. Mostrar ventana en pantalla
            cv2.imshow(f"{settings.PROJECT_NAME} - IA & Movimiento", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('m') or key == ord('M'):
                only_moving_mode = not only_moving_mode
                mode_str = "SOLO EN MOVIMIENTO" if only_moving_mode else "TODOS LOS OBJETOS"
                print(f"🔄 Modo cambiado: {mode_str}")

    except KeyboardInterrupt:
        print("\nDetención solicitada...")
    finally:
        cam.stop()

if __name__ == "__main__":
    main()
