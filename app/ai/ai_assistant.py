"""
Motor de IA Generativa Multimodal para NEXUS VISION.
Conecta con Google Gemini (Vision + LLM) para ver la cámara en tiempo real
y responder cualquier pregunta en lenguaje natural sin restricciones.
"""
import io
from datetime import datetime
from typing import Dict, Any, Optional
from PIL import Image

from app.core.config import settings
from app.database.database import SessionLocal
from app.database.models import EventLog

# Importar Google Generative AI
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class AIAssistant:
    """Asistente de IA con razonamiento visual profundo y conversacional."""

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
                self.gemini_model = genai.GenerativeModel(settings.AI_MODEL_NAME)
                print(f"✨ [AI Assistant] Google Gemini ({settings.AI_MODEL_NAME}) conectado con éxito con Visión Real!")
            except Exception as e:
                print(f"⚠️ Error inicializando Gemini: {e}")
                self.gemini_model = None

    def ask(self, query: str, scene_context: Dict[str, Any], frame_bytes: Optional[bytes] = None) -> str:
        """
        Responde a cualquier pregunta del usuario.
        Si Gemini está configurado, le envía la foto real de la cámara y la pregunta.
        Si no, usa el motor semántico local mejorado.
        """
        # Re-intentar inicializar si se agregó la clave en caliente
        if self.gemini_model is None and settings.GEMINI_API_KEY.strip():
            self._init_gemini()

        # 1. Si Gemini está activo: VISIÓN REAL MULTIMODAL
        if self.gemini_model is not None:
            return self._ask_gemini(query, scene_context, frame_bytes)

        # 2. Si no hay clave de Gemini: Motor conversacional contextual
        return self._ask_local(query, scene_context)

    def _ask_gemini(self, query: str, scene_context: Dict[str, Any], frame_bytes: Optional[bytes]) -> str:
        """Consulta directa a Google Gemini con la imagen en vivo de la cámara."""
        try:
            # Contexto del sistema de seguridad
            inventory_str = ", ".join([f"{k} ({v})" for k, v in scene_context.get("inventory", {}).items()]) or "Ninguno"
            motion_str = f"{scene_context.get('scene_motion', 0.0):.1f}%"
            
            system_prompt = (
                f"Eres Nexus AI, el asistente inteligente y amigable de seguridad y visión artificial de NEXUS VISION.\n"
                f"Estás viendo lo que capta la cámara web del usuario en tiempo real.\n"
                f"- Objetos detectados por el detector local: [{inventory_str}]\n"
                f"- Nivel de movimiento actual: {motion_str}\n"
                f"- Estado del sistema: {scene_context.get('status', 'ONLINE')}\n\n"
                f"Instrucciones:\n"
                f"1. Responde en español de forma natural, amigable, concisa y precisa.\n"
                f"2. Observa con atención la imagen para responder cualquier detalle visual (colores de ropa, gestos, objetos, personas, entorno, etc.).\n"
                f"3. Si el usuario te habla informalmente o pregunta de cualquier tema, mantén una conversación fluida y agradable.\n\n"
                f"Pregunta del usuario: {query}"
            )

            # Cargar imagen si está disponible
            contents = [system_prompt]
            if frame_bytes:
                try:
                    pil_img = Image.open(io.BytesIO(frame_bytes))
                    contents.append(pil_img)
                except Exception:
                    pass

            response = self.gemini_model.generate_content(contents)
            return response.text.strip()

        except Exception as e:
            print(f"⚠️ Error llamando a Gemini API: {e}")
            return f"Lo siento, ocurrió un problema conectando con Gemini: {str(e)[:120]}... Volviendo a respuesta local."

    def _ask_local(self, query: str, ctx: Dict[str, Any]) -> str:
        """Motor conversacional local de contingencia."""
        q = query.lower().strip()
        inventory = ctx.get("inventory", {})
        motion = ctx.get("scene_motion", 0.0)

        # Consultas de visión en vivo
        if any(w in q for w in ["viendo", "ves", "hay", "escena", "frente", "ahora", "que tengo", "que hay", "mira"]):
            if not inventory:
                return "Actualmente la cámara no detecta ningún objeto en movimiento en el plano visual."
            items_desc = [f"{qty} {name}" for name, qty in inventory.items()]
            return f"👁️ **En este momento observo:** {', '.join(items_desc)} (Movimiento: **{motion:.1f}%**)."

        # Consultas de alertas
        elif any(w in q for w in ["alerta", "intrusion", "restringida", "peligro"]):
            return self._query_alerts_history()

        # Consultas de historial
        elif any(w in q for w in ["paso", "ocurrio", "reciente", "historial", "hoy"]):
            return self._query_recent_events()

        # Resumen general
        elif any(w in q for w in ["resumen", "estado", "seguridad", "reporte"]):
            return self._generate_security_report(ctx)

        # Saludos y charla
        elif any(w in q for w in ["hola", "buenas", "que tal", "quien eres"]):
            return (
                "¡Hola! Soy **Nexus AI**. Puedo decirte qué objetos y personas detecto, alertarte de intrusiones y darte reportes de seguridad.\n\n"
                "💡 *Tip:* Para desbloquear inteligencia visual total (reconocer colores de ropa, responder cualquier pregunta libre y razonar), agrega tu clave gratuita de **Gemini** en el archivo `.env`."
            )

        else:
            return (
                f"Te escucho. Actualmente el sistema tiene **{ctx.get('total_items_in_scene', 0)} objetos detectados** "
                f"con **{motion:.1f}% de movimiento**.\n\n"
                "💡 *Para hacerme preguntas completamente libres sobre cualquier tema o detalle de la imagen, activa tu clave gratis de Google Gemini en el archivo `.env`.*"
            )

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
                return "🟢 **Perímetro Seguro**: No se ha registrado ninguna alerta crítica de intrusión durante el día de hoy."

            latest = alerts[0]
            time_diff = int((now - latest.created_at).total_seconds() // 60)
            diff_str = f"hace {time_diff} minutos" if time_diff > 0 else "hace unos instantes"

            return (
                f"🚨 **Reporte de Alertas**: Se han registrado **{len(alerts)} intrusiones** hoy. "
                f"La más reciente fue **{diff_str}** a las **{latest.created_at.strftime('%H:%M:%S')}**, "
                f"donde se detectó un(a) **{latest.object_name}** en la **{latest.zone_name or 'Zona Restringida'}**."
            )
        finally:
            db.close()

    def _query_recent_events(self) -> str:
        db = SessionLocal()
        try:
            events = db.query(EventLog).order_by(EventLog.created_at.desc()).limit(4).all()
            if not events:
                return "La base de datos aún no tiene eventos recientes registrados."

            lines = ["📋 **Últimos eventos registrados:**"]
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

            return (
                "📊 **INFORME DE SEGURIDAD (NEXUS VISION)**\n"
                f"- **Cámara:** {ctx.get('status', 'ONLINE')} ({ctx.get('fps', 0)} FPS)\n"
                f"- **Objetos en Vivo:** {ctx.get('total_items_in_scene', 0)}\n"
                f"- **Eventos hoy:** {total_events}\n"
                f"- **Alertas hoy:** {total_alerts}\n"
                f"- **Diagnóstico:** {'⚠️ Requiere atención' if total_alerts > 0 else '🟢 Seguro'}"
            )
        finally:
            db.close()
