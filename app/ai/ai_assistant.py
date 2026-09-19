"""
Motor de IA Generativa Multimodal Ultra Rápido para NEXUS VISION.
Optimizado con miniatura ultraligera, límite de tokens y llamadas asíncronas para respuestas en < 1 segundo.
"""
import io
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image

from app.core.config import settings
from app.database.database import SessionLocal
from app.database.models import EventLog

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
        if HAS_GENAI and api_key and api_key != "":
            try:
                genai.configure(api_key=api_key)
                # Configuración de generación optimizada para velocidad
                gen_config = genai.types.GenerationConfig(
                    max_output_tokens=180,
                    temperature=0.7
                )
                self.gemini_model = genai.GenerativeModel(
                    settings.AI_MODEL_NAME,
                    generation_config=gen_config
                )
                print(f"✨ [AI Assistant] Google Gemini ({settings.AI_MODEL_NAME}) optimizado y conectado!")
            except Exception as e:
                print(f"⚠️ Error inicializando Gemini: {e}")
                self.gemini_model = None

    async def ask_async(self, query: str, scene_context: Dict[str, Any], frame_bytes: Optional[bytes] = None) -> str:
        """
        Responde de forma asíncrona y no bloqueante.
        """
        if self.gemini_model is None and settings.GEMINI_API_KEY.strip():
            self._init_gemini()

        if self.gemini_model is not None:
            return await self._ask_gemini_async(query, scene_context, frame_bytes)

        return self._ask_local(query, scene_context)

    async def _ask_gemini_async(self, query: str, scene_context: Dict[str, Any], frame_bytes: Optional[bytes]) -> str:
        """Consulta asíncrona ultra rápida a Google Gemini con imagen comprimida."""
        try:
            inventory_str = ", ".join([f"{k} ({v})" for k, v in scene_context.get("inventory", {}).items()]) or "Ninguno"
            motion_str = f"{scene_context.get('scene_motion', 0.0):.1f}%"
            
            system_prompt = (
                f"Eres Nexus AI, asistente de seguridad y visión artificial de NEXUS VISION.\n"
                f"Estás viendo la cámara en vivo. Objetos detectados: [{inventory_str}], Movimiento: {motion_str}.\n"
                f"Instrucciones:\n"
                f"1. Responde en español de forma natural, amigable, concisa (1 o 2 oraciones máximo) y directa.\n"
                f"2. Observa la imagen para detalles visuales (colores, gestos, objetos, personas, ropa).\n\n"
                f"Pregunta: {query}"
            )

            contents = [system_prompt]

            # Optimización de Imagen: Redimensionar a max 512px para subida ultrarrápida (20KB en lugar de 300KB)
            if frame_bytes:
                try:
                    pil_img = Image.open(io.BytesIO(frame_bytes))
                    pil_img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                    contents.append(pil_img)
                except Exception:
                    pass

            # Llamada asíncrona no bloqueante
            response = await self.gemini_model.generate_content_async(contents)
            return response.text.strip()

        except Exception as e:
            print(f"⚠️ Error llamando a Gemini API: {e}")
            return self._ask_local(query, scene_context)

    def _ask_local(self, query: str, ctx: Dict[str, Any]) -> str:
        """Motor conversacional local de contingencia."""
        q = query.lower().strip()
        inventory = ctx.get("inventory", {})
        motion = ctx.get("scene_motion", 0.0)

        if any(w in q for w in ["viendo", "ves", "hay", "escena", "frente", "ahora", "que tengo", "que hay", "mira"]):
            if not inventory:
                return "Actualmente la cámara no detecta ningún objeto en movimiento en el plano visual."
            items_desc = [f"{qty} {name}" for name, qty in inventory.items()]
            return f"👁️ **En este momento observo:** {', '.join(items_desc)} (Movimiento: **{motion:.1f}%**)."

        elif any(w in q for w in ["alerta", "intrusion", "restringida", "peligro"]):
            return self._query_alerts_history()

        elif any(w in q for w in ["paso", "ocurrio", "reciente", "historial", "hoy"]):
            return self._query_recent_events()

        elif any(w in q for w in ["resumen", "estado", "seguridad", "reporte"]):
            return self._generate_security_report(ctx)

        elif any(w in q for w in ["hola", "buenas", "que tal", "quien eres"]):
            return "¡Hola! Soy **Nexus AI**, tu asistente inteligente de seguridad y visión artificial. ¿En qué te ayudo?"

        else:
            return f"Te escucho. Actualmente el sistema tiene **{ctx.get('total_items_in_scene', 0)} objetos detectados** con **{motion:.1f}% de movimiento**."

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
