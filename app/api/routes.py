import time
import base64
from datetime import datetime
from typing import Generator, Any, Optional
import cv2
import numpy as np
from pydantic import BaseModel
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pathlib import Path

from app.services.vision_service import VisionService
from app.services.remote_stream_manager import RemoteStreamManager
from app.services.ip_camera_manager import IPCameraManager
from app.ai.ai_assistant import AIAssistant
from app.database.database import SessionLocal
from app.database.models import EventLog

router = APIRouter()
vision_service = VisionService.get_instance()
remote_stream_manager = RemoteStreamManager.get_instance()
ip_camera_manager = IPCameraManager.get_instance()
ai_assistant = AIAssistant()

class ChatRequest(BaseModel):
    message: str

class CameraSwitchRequest(BaseModel):
    camera_id: Any

class AddIPCameraRequest(BaseModel):
    name: str
    url: str

class TestIPCameraRequest(BaseModel):
    url: str

class RemoteSnapshotUploadRequest(BaseModel):
    image_base64: str
    visitor_name: Optional[str] = "Visitante Remoto"

class RemoteFramePushRequest(BaseModel):
    stream_id: str
    display_name: str
    image_base64: str

def generate_video_stream() -> Generator[bytes, None, None]:
    """Generador de streaming MJPEG de alta fluidez para navegadores web."""
    last_frame_bytes = None
    while True:
        frame_bytes = vision_service.get_latest_jpeg()
        if frame_bytes is not None and frame_bytes is not last_frame_bytes:
            last_frame_bytes = frame_bytes
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.012)

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
def get_event_history(limit: int = 50):
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

@router.delete("/api/events/clear")
def clear_events(camera: Optional[str] = None):
    """Elimina eventos de forma masiva (por cámara o todo el historial) y limpia archivos asociados."""
    db = SessionLocal()
    try:
        query = db.query(EventLog)
        if camera and camera != "ALL":
            query = query.filter(EventLog.zone_name == camera)

        events_to_delete = query.all()
        deleted_count = len(events_to_delete)

        for ev in events_to_delete:
            if ev.snapshot_path:
                try:
                    p = Path(ev.snapshot_path)
                    if p.exists():
                        p.unlink(missing_ok=True)
                except Exception:
                    pass
            db.delete(ev)

        db.commit()
        return {"success": True, "deleted_count": deleted_count, "message": f"Se eliminaron {deleted_count} capturas con éxito."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al limpiar eventos: {str(e)}"}
    finally:
        db.close()

@router.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    """Elimina una captura de seguridad tanto de la base de datos como del disco físico."""
    db = SessionLocal()
    try:
        event = db.query(EventLog).filter(EventLog.id == event_id).first()
        if not event:
            return {"success": False, "message": "Evento no encontrado en la base de datos."}

        # Eliminar archivo de foto del disco físico si existe
        if event.snapshot_path:
            p = Path(event.snapshot_path)
            try:
                if p.exists():
                    p.unlink(missing_ok=True)
                    print(f"🗑️ Archivo físico de imagen eliminado: {p.name}")
            except Exception as file_err:
                print(f"⚠️ Error eliminando archivo físico {event.snapshot_path}: {file_err}")

        db.delete(event)
        db.commit()
        return {"success": True, "message": f"Captura #{event_id} eliminada correctamente."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Error al eliminar el evento: {str(e)}"}
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

@router.post("/api/toggle_auto_snapshot")
def toggle_auto_snapshot():
    new_state = vision_service.toggle_auto_snapshot()
    return {"auto_snapshot": new_state}

@router.post("/api/snapshot")
def take_manual_snapshot():
    """Toma una foto instantánea desde la cámara y la guarda en BD/storage."""
    res = vision_service.take_snapshot(description="Captura Manual desde Dashboard", object_name="Captura Manual")
    if res:
        return {"success": True, "data": res}
    return {"success": False, "message": "No se pudo tomar la captura (cámara inactiva)."}

@router.post("/api/upload_remote_snapshot")
def upload_remote_snapshot(req: RemoteSnapshotUploadRequest):
    """Guarda una foto tomada por la cámara frontal del navegador del visitante."""
    try:
        raw_data = req.image_base64
        if "," in raw_data:
            raw_data = raw_data.split(",", 1)[1]
        image_bytes = base64.b64decode(raw_data)
        
        snapshots_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "snapshots"
        now = datetime.now()
        cam_folder = "camara_amigos_visitantes"
        date_folder = snapshots_dir / cam_folder / now.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)
        
        filename = f"entrada_{now.strftime('%H%M%S_%f')[:10]}.jpg"
        filepath = date_folder / filename
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
            
        web_url = f"/snapshots/{cam_folder}/{now.strftime('%Y-%m-%d')}/{filename}"
        
        db = SessionLocal()
        try:
            visitor_label = req.visitor_name or "Visitante Remoto"
            event = EventLog(
                event_type="REMOTE_VISITOR",
                object_name=f"{visitor_label} [Amigo]",
                confidence=1.0,
                camera_id=0,
                zone_name=f"🌐 {visitor_label}",
                alert_level="INFO",
                description=f"Acceso registrado de visitante remoto ({visitor_label})",
                snapshot_path=str(filepath),
                created_at=now
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            print(f"📸 [VISITANTE REMOTO #{event.id}] Captura guardada en '{cam_folder}': {filepath.name}")
            return {
                "success": True,
                "data": {
                    "id": event.id,
                    "snapshot_url": web_url,
                    "time": now.strftime("%H:%M:%S"),
                    "date": now.strftime("%Y-%m-%d")
                }
            }
        except Exception as err:
            db.rollback()
            return {"success": False, "message": str(err)}
        finally:
            db.close()
    except Exception as e:
        return {"success": False, "message": f"Error procesando imagen: {e}"}

@router.post("/api/remote_stream/push")
def push_remote_frame(req: RemoteFramePushRequest):
    """Recibe un fotograma en vivo desde la cámara remota del amigo/dispositivo."""
    try:
        if remote_stream_manager.is_expelled(req.stream_id):
            return {"status": "expelled", "message": "Transmisión finalizada por el anfitrión."}

        raw_data = req.image_base64
        if "," in raw_data:
            raw_data = raw_data.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is not None:
            allowed = remote_stream_manager.register_or_update_frame(
                stream_id=req.stream_id,
                display_name=req.display_name,
                frame=frame
            )
            if not allowed:
                return {"status": "expelled", "message": "Transmisión finalizada por el anfitrión."}
            return {"status": "ok"}
        return {"status": "error", "message": "No se pudo decodificar la imagen"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/remote_stream/status/{stream_id}")
def check_stream_status(stream_id: str):
    """Verifica si la transmisión remota sigue permitida o fue expulsada."""
    return {"expelled": remote_stream_manager.is_expelled(stream_id)}

@router.post("/api/remote_stream/expel/{stream_id}")
def expel_remote_stream(stream_id: str):
    """Expulsa la transmisión remota desde el panel del anfitrión."""
    success = remote_stream_manager.expel_stream(stream_id)
    # Si la cámara activa en visión era esta, revertir a cámara 0
    if str(vision_service.cam.camera_index) == stream_id:
        vision_service.switch_camera(0)
    return {"success": success, "message": f"Dispositivo '{stream_id}' desconectado exitosamente."}

@router.post("/api/remote_stream/snapshot/{stream_id}")
def take_remote_snapshot(stream_id: str):
    """Toma una foto instantánea directamente de la cámara del amigo conectado."""
    frame = remote_stream_manager.get_frame(stream_id)
    if frame is None:
        return {"success": False, "message": "No hay señal de video de este dispositivo actualmente."}

    now = datetime.now()
    cam_folder = f"camara_amigo_{stream_id.replace('remote_disp_', '').replace('remote_', '')}"
    snapshots_dir = Path(__file__).resolve().parent.parent.parent / "storage" / "snapshots"
    date_folder = snapshots_dir / cam_folder / now.strftime("%Y-%m-%d")
    date_folder.mkdir(parents=True, exist_ok=True)

    filename = f"manual_{now.strftime('%H%M%S_%f')[:10]}.jpg"
    filepath = date_folder / filename

    cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    web_url = f"/snapshots/{cam_folder}/{now.strftime('%Y-%m-%d')}/{filename}"

    clean_disp = stream_id.replace('remote_disp_', 'Amigo #')
    db = SessionLocal()
    try:
        event = EventLog(
            event_type="REMOTE_SNAPSHOT",
            object_name=f"Captura de Amigo [{clean_disp}]",
            confidence=1.0,
            camera_id=0,
            zone_name=f"🌐 {clean_disp}",
            alert_level="INFO",
            description=f"Captura instantánea tomada a {clean_disp}",
            snapshot_path=str(filepath),
            created_at=now
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return {
            "success": True,
            "data": {
                "id": event.id,
                "snapshot_url": web_url,
                "time": now.strftime("%H:%M:%S"),
                "date": now.strftime("%Y-%m-%d")
            }
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}
    finally:
        db.close()

@router.get("/api/remote_stream/devices")
def get_connected_devices():
    """Retorna la lista de dispositivos remotos conectados activamente."""
    return remote_stream_manager.get_active_streams_detail()

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

@router.get("/api/ip_cameras")
def list_ip_cameras():
    """Retorna la lista de cámaras de seguridad IP / RTSP registradas."""
    return ip_camera_manager.get_cameras()

@router.post("/api/ip_cameras/test")
def test_ip_camera(req: TestIPCameraRequest):
    """Prueba la conexión a una URL RTSP o IP antes de agregarla."""
    if not req.url or not req.url.strip():
        return {"success": False, "message": "Por favor ingresa una URL RTSP o IP válida."}
    success, msg = ip_camera_manager.test_connection(req.url.strip())
    return {"success": success, "message": msg}

@router.post("/api/ip_cameras/add")
def add_ip_camera(req: AddIPCameraRequest):
    """Agrega una nueva cámara de seguridad IP o stream RTSP."""
    if not req.url or not req.url.strip():
        return {"success": False, "message": "La URL del stream no puede estar vacía."}
    new_cam = ip_camera_manager.add_camera(name=req.name, url=req.url)
    return {
        "success": True,
        "message": f"Cámara '{new_cam['name']}' registrada exitosamente.",
        "camera": new_cam
    }

@router.delete("/api/ip_cameras/{camera_id}")
def delete_ip_camera(camera_id: str):
    """Elimina una cámara IP del catálogo."""
    success = ip_camera_manager.remove_camera(camera_id)
    if str(vision_service.cam.camera_index) == camera_id:
        vision_service.switch_camera(0)
    return {"success": success, "message": "Cámara eliminada correctamente." if success else "Cámara no encontrada."}

@router.get("/api/public_cameras")
def get_public_cameras():
    """Retorna las cámaras públicas y abiertas precargadas en el sistema."""
    return IPCameraManager.get_preset_public_cameras()

@router.post("/api/public_cameras/connect/{pub_id}")
def connect_public_camera(pub_id: str):
    """Conecta directamente a una de las cámaras públicas precargadas."""
    presets = IPCameraManager.get_preset_public_cameras()
    cam = next((c for c in presets if c["id"] == pub_id), None)
    if not cam:
        return {"success": False, "message": "Cámara pública no encontrada."}
    
    # Verificar si ya existe en catálogo
    existing = next((c for c in ip_camera_manager.get_cameras() if c["url"] == cam["url"]), None)
    if not existing:
        saved_cam = ip_camera_manager.add_camera(name=cam["name"], url=cam["url"])
        cam_id = saved_cam["id"]
    else:
        cam_id = existing["id"]

    success = vision_service.switch_camera(cam_id)
    if not success:
        return {
            "success": False,
            "message": f"El servidor externo de '{cam['name']}' no responde (apagado o con firewall). Selecciona la 'Cámara CCTV Tráfico Garantizada 24/7' o conecta tu propia cámara IP."
        }

    return {
        "success": True,
        "camera_id": cam_id,
        "name": cam["name"],
        "message": f"Conectado a la cámara: {cam['name']}"
    }


