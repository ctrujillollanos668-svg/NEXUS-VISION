"""
Motor de IA Generativa Multimodal Ultra Rápido para NEXUS VISION.
Optimizado con miniatura ultraligera, límite de tokens y llamadas asíncronas para respuestas en < 1 segundo.
"""
import io
import asyncio
import warnings
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image

from app.core.config import settings
from app.database.database import SessionLocal
from app.database.models import EventLog

warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class AIAssistant:
    """Asistente de IA con razonamiento visual profundo y ultra veloz."""

    def __init__(self):
        self.name = "Nexus AI"
        self.gemini_model = None
        self._init_gemini()

    def _init_gemini(self):
        """Inicializa Google Gemini si la clave API está configurada en .env."""
        api_key = settings.GEMINI_API_KEY.strip()
        if HAS_GENAI and api_key and api_key.startswith("AIzaSy"):
            try:
                genai.configure(api_key=api_key)
                # Configuración de generación optimizada para velocidad y completitud
                gen_config = genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.7
                )
                model_name = "gemini-1.5-flash" if "3.6" in settings.AI_MODEL_NAME else settings.AI_MODEL_NAME
                self.gemini_model = genai.GenerativeModel(
                    model_name,
                    generation_config=gen_config
                )
                print(f"✨ [AI Assistant] Google Gemini ({model_name}) optimizado y conectado!")
            except Exception as e:
                print(f"⚠️ Error inicializando Gemini: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None

    async def ask_async(self, query: str, scene_context: Dict[str, Any], frame_bytes: Optional[bytes] = None) -> str:
        """
        Responde de forma asíncrona y no bloqueante con timeout estricto de 3.5 segundos.
        """
        if self.gemini_model is not None:
            try:
                return await asyncio.wait_for(
                    self._ask_gemini_async(query, scene_context, frame_bytes),
                    timeout=3.5
                )
            except Exception as e:
                print(f"⚠️ Timeout o error en Gemini ({e}), usando motor local instantáneo.")
                return self._ask_local(query, scene_context)

        return self._ask_local(query, scene_context)

    async def _ask_gemini_async(self, query: str, scene_context: Dict[str, Any], frame_bytes: Optional[bytes]) -> str:
        """Consulta asíncrona ultra rápida a Google Gemini con imagen comprimida."""
        try:
            inventory_str = ", ".join([f"{k} ({v})" for k, v in scene_context.get("inventory", {}).items()]) or "Sin objetos identificados"
            motion_str = f"{scene_context.get('scene_motion', 0.0):.1f}%"
            
            system_prompt = (
                f"Eres Nexus AI, el asistente inteligente de visión artificial y seguridad de NEXUS VISION.\n"
                f"Estás analizando la transmisión de la cámara en vivo. Contexto de telemetría: [{inventory_str}], Nivel de movimiento: {motion_str}.\n"
                f"Instrucciones:\n"
                f"1. Responde siempre en español con frases completas, claras, fluidas y amigables.\n"
                f"2. Si el usuario pregunta qué ves o qué hay, describe detalladamente los objetos, la persona, lo que tiene en las manos, gestos, colores y el entorno visible en la imagen.\n"
                f"3. Responde en un solo párrafo conciso.\n\n"
                f"Pregunta del usuario: {query}"
            )

            contents = [system_prompt]

            if frame_bytes:
                try:
                    pil_img = Image.open(io.BytesIO(frame_bytes))
                    pil_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                    contents.append(pil_img)
                except Exception:
                    pass

            response = await self.gemini_model.generate_content_async(contents)
            text_result = response.text.strip() if response and response.text else ""
            if text_result:
                return text_result
            return self._ask_local(query, scene_context)

        except Exception as e:
            print(f"⚠️ Error llamando a Gemini API: {e}")
            return self._ask_local(query, scene_context)

    def _ask_local(self, query: str, ctx: Dict[str, Any]) -> str:
        """Motor conversacional local de contingencia con comprensión robusta e instantánea."""
        q = query.lower().strip()
        inventory = ctx.get("inventory", {})
        motion = ctx.get("scene_motion", 0.0)

        if any(w in q for w in ["foto", "captura", "snapshot", "fotografia", "toma una foto", "saca una foto"]):
            from app.services.vision_service import VisionService
            vs = VisionService.get_instance()
            res = vs.take_snapshot(description="Captura por comando de voz/chat", object_name="Captura Asistente")
            if res:
                return f"📸 ¡Foto capturada con éxito! La imagen ha sido guardada en la base de datos y en tu historial a las {res.get('time')}."
            return "No pude tomar la foto en este momento porque la cámara no está lista."

        elif any(w in q for w in ["viendo", "ves", "hay", "escena", "frente", "ahora", "que tengo", "que hay", "mira", "mirando", "dime", "observas"]):
            if not inventory:
                return f"En este momento la cámara está en línea con {motion:.1f}% de movimiento, pero no distingo objetos ni personas en el plano central."
            items_desc = [f"{qty} {name}" for name, qty in inventory.items()]
            return f"👁️ En este momento observo en la cámara: {', '.join(items_desc)}, con un nivel de movimiento en sala del {motion:.1f}%."

        elif any(w in q for w in ["alerta", "intrusion", "restringida", "peligro"]):
            return self._query_alerts_history()

        elif any(w in q for w in ["paso", "ocurrio", "reciente", "historial", "hoy"]):
            return self._query_recent_events()

        elif any(w in q for w in ["resumen", "estado", "seguridad", "reporte"]):
            return self._generate_security_report(ctx)

        elif any(w in q for w in ["hola", "buenas", "que tal", "quien eres"]):
            return "¡Hola! Soy Nexus AI, tu asistente inteligente de seguridad y visión artificial. ¿En qué te puedo colaborar hoy?"

        else:
            if inventory:
                items_desc = [f"{qty} {name}" for name, qty in inventory.items()]
                return f"Te escucho. En la escena detecto {', '.join(items_desc)} con {motion:.1f}% de movimiento en sala."
            return f"Te escucho. El sistema se encuentra en línea y vigilando activamente a {ctx.get('fps', 0)} FPS."

    def _query_alerts_history(self) -> str:
        db = SessionLocal()
        try:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            alerts = db.query(EventLog).filter(
                EventLog.alert_level == "ALERT",
                EventLog.created_at >= today_start
            ).order_by(EventLog.created_at.desc()).limit(5).all()

            if not alerts:
                return "🟢 **Perímetro Seguro**: No se ha registrado ninguna alerta crítica de intrusión hoy."

            latest = alerts[0]
            time_diff = int((now - latest.created_at).total_seconds() // 60)
            diff_str = f"hace {time_diff} minutos" if time_diff > 0 else "hace instantes"

            return f"🚨 Se registraron **{len(alerts)} intrusiones** hoy. La última fue {diff_str} por un(a) **{latest.object_name}** en **{latest.zone_name or 'Zona Restringida'}**."
        finally:
            db.close()

    def _query_recent_events(self) -> str:
        db = SessionLocal()
        try:
            events = db.query(EventLog).order_by(EventLog.created_at.desc()).limit(4).all()
            if not events:
                return "No hay eventos recientes registrados."

            lines = ["📋 **Últimos eventos:**"]
            for e in events:
                tag = "🚨 ALERTA" if e.alert_level == "ALERT" else "📸 DETECCIÓN"
                lines.append(f"- **{e.created_at.strftime('%H:%M:%S')}** | {tag}: {e.object_name} ({int((e.confidence or 0)*100)}%)")

            return "\n".join(lines)
        finally:
            db.close()

    def _generate_security_report(self, ctx: Dict[str, Any]) -> str:
        db = SessionLocal()
        try:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            total_events = db.query(EventLog).filter(EventLog.created_at >= today_start).count()
            total_alerts = db.query(EventLog).filter(EventLog.alert_level == "ALERT", EventLog.created_at >= today_start).count()

            return f"📊 **Reporte Rápido:** {ctx.get('total_items_in_scene', 0)} objetos en vivo | {total_events} eventos hoy | {total_alerts} alertas | Estado: {'⚠️ Atención' if total_alerts > 0 else '🟢 Seguro'}"
        finally:
            db.close()
