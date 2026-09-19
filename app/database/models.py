"""
Modelos y Tablas de la Base de Datos NEXUS VISION.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database.database import Base

class EventLog(Base):
    """Tabla para registrar eventos de detección y alertas."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)   # Ej: PERSONA_DETECTADA
    object_name = Column(String(50), nullable=False)             # Ej: Persona, Celular, Lapicero
    confidence = Column(Float, nullable=False)                   # Ej: 0.89
    camera_id = Column(Integer, default=0)
    description = Column(String(255), nullable=True)
    snapshot_path = Column(String(255), nullable=True)           # Ruta de la foto .jpg
    created_at = Column(DateTime, default=datetime.now, index=True)

    def __repr__(self):
        return f"<EventLog id={self.id} type={self.event_type} object={self.object_name} time={self.created_at}>"
