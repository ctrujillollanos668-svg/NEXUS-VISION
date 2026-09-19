"""
Pruebas para los Endpoints de la API REST (FastAPI).
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Verifica que la raíz sirva el Dashboard HTML."""
    response = client.get("/")
    assert response.status_code == 200
    assert "NEXUS VISION" in response.text

def test_api_stats_endpoint():
    """Verifica que el endpoint /api/stats retorne métricas válidas."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "fps" in data
    assert "inference_ms" in data
    assert "device_name" in data
    assert "categories" in data

def test_api_events_endpoint():
    """Verifica que el endpoint /api/events retorne una lista."""
    response = client.get("/api/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_cameras_endpoint():
    """Verifica que el endpoint /api/cameras retorne las cámaras."""
    response = client.get("/api/cameras")
    assert response.status_code == 200
    data = response.json()
    assert "cameras" in data
    assert "current_camera" in data

def test_api_toggle_motion():
    """Verifica conmutación de filtro de movimiento."""
    response = client.post("/api/toggle_motion")
    assert response.status_code == 200
    assert "only_moving" in response.json()

def test_api_toggle_zones():
    """Verifica conmutación de zonas de seguridad."""
    response = client.post("/api/toggle_zones")
    assert response.status_code == 200
    assert "zones_enabled" in response.json()
