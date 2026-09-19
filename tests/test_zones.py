"""
Pruebas para el Administrador de Zonas de Seguridad (ZoneManager).
"""
import pytest
from app.zones.zone_manager import ZoneManager, SecurityZone

def test_zone_manager_defaults():
    """Verifica que ZoneManager cargue las zonas predeterminadas."""
    zm = ZoneManager()
    assert zm.enabled is True
    assert "restricted_zone_1" in zm.zones
    assert zm.zones["restricted_zone_1"].name == "ZONA RESTRINGIDA"

def test_zone_intersection_inside():
    """Verifica detección positiva cuando un bbox está dentro de la zona."""
    zm = ZoneManager()
    frame_w, frame_h = 1000, 1000
    # La zona predeterminada está entre x: 550 a 980, y: 150 a 850
    bbox_inside = (600, 200, 700, 300)
    
    intrusions = zm.check_intrusions(bbox_inside, frame_w, frame_h)
    assert len(intrusions) == 1
    assert intrusions[0].id == "restricted_zone_1"

def test_zone_intersection_outside():
    """Verifica que no detecte intrusión si el bbox está fuera de la zona."""
    zm = ZoneManager()
    frame_w, frame_h = 1000, 1000
    # Bbox en sector izquierdo (x: 50 a 150)
    bbox_outside = (50, 50, 150, 150)
    
    intrusions = zm.check_intrusions(bbox_outside, frame_w, frame_h)
    assert len(intrusions) == 0

def test_zone_disabled():
    """Verifica que si la zona está desactivada, no genere alertas."""
    zm = ZoneManager()
    zm.enabled = False
    frame_w, frame_h = 1000, 1000
    bbox_inside = (600, 200, 700, 300)
    
    intrusions = zm.check_intrusions(bbox_inside, frame_w, frame_h)
    assert len(intrusions) == 0
