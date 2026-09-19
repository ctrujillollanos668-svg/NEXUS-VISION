"""
Pruebas para la Base de Datos SQLite y Modelos de Seguridad.
"""
from datetime import datetime
import pytest
from app.database.database import SessionLocal, init_db
from app.database.models import EventLog

def test_database_init():
    """Verifica que las tablas se creen correctamente en SQLite."""
    init_db()
    db = SessionLocal()
    try:
        assert db is not None
    finally:
        db.close()

def test_insert_and_query_event():
    """Verifica la inserción y consulta de eventos de seguridad."""
    init_db()
    db = SessionLocal()
    try:
        new_event = EventLog(
            event_type="TEST_INTRUSION",
            object_name="Persona de Prueba",
            confidence=0.98,
            camera_id=0,
            zone_name="Zona de Pruebas",
            alert_level="ALERT",
            description="Evento de prueba unitaria",
            created_at=datetime.utcnow()
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        assert new_event.id is not None
        assert new_event.object_name == "Persona de Prueba"

        # Consultar
        retrieved = db.query(EventLog).filter(EventLog.id == new_event.id).first()
        assert retrieved is not None
        assert retrieved.event_type == "TEST_INTRUSION"

        # Limpiar registro de test
        db.delete(retrieved)
        db.commit()
    finally:
        db.close()
