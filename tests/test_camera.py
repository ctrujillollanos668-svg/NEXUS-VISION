"""
Pruebas para el Módulo de Cámara (CameraManager).
"""
import pytest
from app.camera.camera_manager import CameraManager

def test_camera_manager_initialization():
    """Verifica que CameraManager se inicialice con valores por defecto."""
    cam = CameraManager(camera_index=0, target_fps=30)
    assert cam.camera_index == 0
    assert cam.target_fps == 30
    assert not cam.is_running
    assert cam.fps == 0.0

def test_list_available_cameras():
    """Verifica que el escáner de cámaras retorne una lista válida."""
    cams = CameraManager.list_available_cameras(max_tested=2)
    assert isinstance(cams, list)
    for cam in cams:
        assert "id" in cam
        assert "name" in cam
        assert "type" in cam
