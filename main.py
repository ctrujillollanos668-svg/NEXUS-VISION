"""
NEXUS VISION — Sistema de Cámara Inteligente con IA
Detección Universal, Filtro de Movimiento, Zonas Restringidas, Alertas Tácticas y Base de Datos.
"""
import os
import cv2
from app.core.config import settings
from app.database.database import init_db
from app.camera.camera_manager import CameraManager
from app.detection.detector import ObjectDetector
from app.detection.motion_detector import MotionDetector
from app.zones.zone_manager import ZoneManager
from app.alerts.alert_manager import AlertManager

def main():
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} — v{settings.VERSION}")
    print("=" * 60)

    # 1. Inicializar Base de Datos SQLite
    init_db()

    # 2. Iniciar Detector de Inteligencia Artificial Universal
    detector = ObjectDetector(
        model_path=settings.MODEL_PATH,
        conf_threshold=settings.CONFIDENCE_THRESHOLD,
        iou_threshold=settings.IOU_THRESHOLD
    )

    # 3. Iniciar Detector de Movimiento
    motion_detector = MotionDetector()

    # 4. Iniciar Gestor de Zonas de Seguridad
    zone_manager = ZoneManager()

    # 5. Iniciar Gestor de Alertas y Sonido
    alert_manager = AlertManager(
        cooldown_seconds=settings.ALERT_COOLDOWN_SECONDS,
        enable_sound=settings.ENABLE_ALERT_SOUND,
        camera_id=settings.CAMERA_INDEX
    )

    # 6. Iniciar Administrador de Cámara
    cam = CameraManager(
        camera_index=settings.CAMERA_INDEX,
        target_fps=settings.TARGET_FPS
    )

    if not cam.start():
        return

    only_moving_mode = settings.ONLY_MOVING_OBJECTS

    print("📺 Sistema de Vigilancia Activo con ZONA RESTRINGIDA.")
    print(f"⏱️ Cooldown de alertas configurado en: {settings.ALERT_COOLDOWN_SECONDS} segundos.")
    print("💡 Atajos de teclado:")
    print("   - 'm': Alternar entre 'Solo Objetos en Movimiento' y 'Todos los Objetos'")
    print("   - 'q' o ESC: Salir")

    try:
        while cam.is_running:
            success, frame = cam.read_frame()
            if not success:
                break

            # 7. Actualizar mapa de movimiento
            _, scene_motion = motion_detector.update(frame)

            # 8. Detectar objetos
            detections, category_counts, inventory = detector.detect(
                frame=frame,
                motion_detector=motion_detector,
                only_moving=only_moving_mode,
                min_motion_ratio=settings.MIN_MOTION_RATIO
            )

            # 9. Evaluar reglas de intrusión en Zonas Restringidas
            active_zones, alert_banner = alert_manager.evaluate_rules(
                frame=frame,
                detections=detections,
                zone_manager=zone_manager
            )

            # 10. Dibujar Zonas de Seguridad (brillan en rojo si hay intrusión)
            frame = zone_manager.draw_zones(frame, active_alerts=active_zones)

            # 11. Dibujar Bounding Boxes de los objetos
            frame = detector.draw_detections(frame, detections, only_moving=only_moving_mode)

            # 12. Dibujar HUD, banner de alerta e inventario
            frame = cam.draw_hud(
                frame=frame,
                category_counts=category_counts,
                inventory=inventory,
                only_moving=only_moving_mode,
                scene_motion=scene_motion,
                event_alert=alert_banner
            )

            # 13. Mostrar video en vivo
            cv2.imshow(f"{settings.PROJECT_NAME} - Sistema de Seguridad y Zonas", frame)

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
