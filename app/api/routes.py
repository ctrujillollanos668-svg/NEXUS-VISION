"""
Rutas y Endpoints Web para NEXUS VISION.
"""
import time
from typing import Generator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pathlib import Path

from app.services.vision_service import VisionService
from app.database.database import SessionLocal
from app.database.models import EventLog

router = APIRouter()
vision_service = VisionService.get_instance()

def generate_video_stream() -> Generator[bytes, None, None]:
    """Generador de streaming MJPEG para navegadores web."""
    while True:
        frame_bytes = vision_service.get_latest_jpeg()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.03)

@router.get("/video_feed")
def video_feed():
    """Endpoint de transmisión de video en vivo (MJPEG)."""
    return StreamingResponse(
        generate_video_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/api/stats")
def get_live_stats():
    """Retorna las estadísticas en tiempo real del sistema."""
    return vision_service.get_stats()

@router.get("/api/events")
def get_event_history(limit: int = 30):
    """Retorna el historial de eventos y alertas guardados en la base de datos."""
    db = SessionLocal()
    try:
        events = db.query(EventLog).order_by(EventLog.created_at.desc()).limit(limit).all()
        result = []
        for e in events:
            web_snapshot_url = None
            if e.snapshot_path:
                p = Path(e.snapshot_path)
                try:
                    parts = p.parts
                    if "snapshots" in parts:
                        idx = parts.index("snapshots")
                        web_snapshot_url = "/snapshots/" + "/".join(parts[idx+1:])
                except Exception:
                    web_snapshot_url = None

            result.append({
                "id": e.id,
                "event_type": e.event_type,
                "object_name": e.object_name,
                "confidence": round((e.confidence or 0.0) * 100, 1),
                "camera_id": e.camera_id,
                "zone_name": getattr(e, "zone_name", "Zona General"),
                "alert_level": getattr(e, "alert_level", "INFO"),
                "description": e.description,
                "snapshot_url": web_snapshot_url,
                "time": e.created_at.strftime("%H:%M:%S") if e.created_at else "--:--:--",
                "date": e.created_at.strftime("%Y-%m-%d") if e.created_at else "----/--/--"
            })
        return result
    except Exception as err:
        print(f"⚠️ Error consultando eventos: {err}")
        return []
    finally:
        db.close()

@router.post("/api/toggle_motion")
def toggle_motion():
    new_state = vision_service.toggle_motion()
    return {"only_moving": new_state}

@router.post("/api/toggle_sound")
def toggle_sound():
    new_state = vision_service.toggle_sound()
    return {"sound_enabled": new_state}

@router.post("/api/toggle_zones")
def toggle_zones():
    new_state = vision_service.toggle_zones()
    return {"zones_enabled": new_state}
