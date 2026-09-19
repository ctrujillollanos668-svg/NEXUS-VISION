"""
Rutas y Endpoints Web para NEXUS VISION.
"""
import time
from typing import Generator, Any
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pathlib import Path

from app.services.vision_service import VisionService
from app.ai.ai_assistant import AIAssistant
from app.database.database import SessionLocal
from app.database.models import EventLog

router = APIRouter()
vision_service = VisionService.get_instance()
ai_assistant = AIAssistant()

class ChatRequest(BaseModel):
    message: str

class CameraSwitchRequest(BaseModel):
    camera_id: Any

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
                    if p.exists():
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

@router.post("/api/chat")
async def ask_ai(req: ChatRequest):
    """Endpoint asíncrono ultra veloz para el Asistente de IA."""
    scene_context = vision_service.get_stats()
    latest_frame = vision_service.get_latest_jpeg()
    response_text = await ai_assistant.ask_async(req.message, scene_context, frame_bytes=latest_frame)
    return {
        "reply": response_text,
        "time": time.strftime("%H:%M:%S")
    }

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

@router.get("/api/cameras")
def get_cameras():
    """Retorna la lista de cámaras detectadas en el sistema."""
    return vision_service.list_cameras()

@router.post("/api/cameras/switch")
def switch_camera(req: CameraSwitchRequest):
    """Cambia la cámara activa del sistema."""
    success = vision_service.switch_camera(req.camera_id)
    return {
        "success": success,
        "camera_id": req.camera_id,
        "message": f"Cámara cambiada exitosamente a '{req.camera_id}'." if success else f"Error al cambiar a cámara '{req.camera_id}'."
    }

