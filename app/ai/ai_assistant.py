"""
Motor de IA Generativa y Razonamiento Contextual para NEXUS VISION.
Interpreta en tiempo real lo que ve la cámara y analiza el historial de eventos en SQLite.
"""
from datetime import datetime
from typing import Dict, Any, List
from app.database.database import SessionLocal
from app.database.models import EventLog

class AIAssistant:
    """Asistente inteligente con razonamiento sobre la escena y la seguridad."""

    def __init__(self):
        self.name = "Nexus AI"

    def ask(self, query: str, scene_context: Dict[str, Any]) -> str:
        """
        Procesa una pregunta del usuario combinando el estado en vivo de la cámara
        y las consultas a la base de datos de eventos.
        """
        q = query.lower().strip()

        # 1. Preguntas sobre qué está viendo en vivo la cámara
        if any(w in q for w in ["viendo", "ves", "hay", "escena", "frente", "ahora", "que tengo", "que hay"]):
            return self._describe_current_scene(scene_context)

        # 2. Preguntas sobre alertas e intrusiones
        elif any(w in q for w in ["alerta", "intrusion", "restringida", "peligro", "infraccion"]):
            return self._query_alerts_history()

        # 3. Preguntas sobre eventos recientes / historial
        elif any(w in q for w in ["paso", "ocurrio", "reciente", "historial", "ultimamente", "minutos", "hoy"]):
            return self._query_recent_events()

        # 4. Preguntas sobre personas o movimiento
        elif any(w in q for w in ["persona", "gente", "alguien", "movimiento"]):
            return self._query_people_and_motion(scene_context)

        # 5. Resumen general de seguridad
        elif any(w in q for w in ["resumen", "estado", "seguridad", "informe", "reporte"]):
            return self._generate_security_report(scene_context)

        # 6. Saludo o presentación
        elif any(w in q for w in ["hola", "quien eres", "buenas", "ayuda", "nexus"]):
            return (
                f"¡Hola! Soy **{self.name}**, tu asistente de seguridad y visión artificial. "
                "Puedo decirte qué objetos y personas están frente a la cámara en este instante, "
                "consultar el historial de alertas en la base de datos o darte un informe de seguridad."
            )

        # 7. Respuesta contextual por defecto
        else:
            return (
                f"Entendido. En este momento el sistema está **{scene_context.get('status', 'ONLINE')}** "
                f"con **{scene_context.get('total_items_in_scene', 0)} objetos** detectados en la escena. "
                "Puedes preguntarme por ejemplo: *'¿Qué estás viendo?'*, *'¿Ocurrió alguna alerta?'* o *'Haz un resumen de seguridad'*."
            )

    def _describe_current_scene(self, ctx: Dict[str, Any]) -> str:
        inventory = ctx.get("inventory", {})
        fps = ctx.get("fps", 0.0)
        motion = ctx.get("scene_motion", 0.0)

        if not inventory or len(inventory) == 0:
            return "Actualmente la cámara no detecta ningún objeto ni persona en el plano visual (el espacio se encuentra vacío o inmóvil)."

        items_desc = []
        for name, qty in inventory.items():
            if qty == 1:
                items_desc.append(f"1 {name}")
            else:
                items_desc.append(f"{qty} {name}s")

        items_str = ", ".join(items_desc)
        motion_state = f"con un **{motion:.1f}%** de movimiento en la sala" if motion > 2.0 else "completamente en reposo"

        return f"👁️ **En este momento observo:** {items_str}, {motion_state} (transmitiendo a **{fps:.1f} FPS**)."

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
                return "🟢 **Estado Seguro**: No se ha registrado ninguna alerta crítica de intrusión durante el día de hoy."

            latest = alerts[0]
            time_diff = int((now - latest.created_at).total_seconds() // 60)
            diff_str = f"hace {time_diff} minutos" if time_diff > 0 else "hace unos instantes"

            return (
                f"🚨 **Reporte de Alertas**: Se han registrado **{len(alerts)} intrusiones** hoy. "
                f"La más reciente fue **{diff_str}** a las **{latest.created_at.strftime('%H:%M:%S')}**, "
                f"donde se detectó un(a) **{latest.object_name}** violando la **{latest.zone_name or 'Zona Restringida'}**."
            )
        finally:
            db.close()

    def _query_recent_events(self) -> str:
        db = SessionLocal()
        try:
            events = db.query(EventLog).order_by(EventLog.created_at.desc()).limit(4).all()
            if not events:
                return "La base de datos aún no tiene eventos recientes registrados."

            lines = ["📋 **Últimos eventos registrados en la base de datos:**"]
            for e in events:
                tag = "🚨 ALERTA" if e.alert_level == "ALERT" else "📸 DETECCIÓN"
                lines.append(f"- **{e.created_at.strftime('%H:%M:%S')}** | {tag}: {e.object_name} ({int((e.confidence or 0)*100)}% certeza) en {e.zone_name or 'Cámara'}")

            return "\n".join(lines)
        finally:
            db.close()

    def _query_people_and_motion(self, ctx: Dict[str, Any]) -> str:
        cats = ctx.get("categories", {})
        persons = cats.get("person", 0)
        motion = ctx.get("scene_motion", 0.0)

        if persons > 0:
            return f"👤 Se detecta **{persons} persona(s)** en la escena en este momento con un movimiento de sala del **{motion:.1f}%**."
        else:
            return f"No hay personas frente a la cámara en este instante. Movimiento ambiental: **{motion:.1f}%**."

    def _generate_security_report(self, ctx: Dict[str, Any]) -> str:
        db = SessionLocal()
        try:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            total_events = db.query(EventLog).filter(EventLog.created_at >= today_start).count()
            total_alerts = db.query(EventLog).filter(EventLog.alert_level == "ALERT", EventLog.created_at >= today_start).count()

            return (
                "📊 **INFORME GENERAL DE SEGURIDAD (NEXUS VISION)**\n"
                f"- **Estado de Transmisión:** {ctx.get('status', 'ONLINE')} ({ctx.get('fps', 0)} FPS)\n"
                f"- **Objetos en Vivo:** {ctx.get('total_items_in_scene', 0)} detectados\n"
                f"- **Zona Restringida:** {'ACTIVA 🛡️' if ctx.get('zones_enabled', True) else 'DESACTIVADA'}\n"
                f"- **Eventos registrados hoy:** {total_events}\n"
                f"- **Alertas de Intrusión hoy:** {total_alerts}\n"
                f"- **Diagnóstico:** {'⚠️ Alertas detectadas hoy' if total_alerts > 0 else '🟢 Perímetro Seguro sin anomalías'}"
            )
        finally:
            db.close()
