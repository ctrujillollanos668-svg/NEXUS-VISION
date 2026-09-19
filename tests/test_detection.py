"""
Pruebas para el Módulo de Detección de Objetos e Inteligencia Artificial.
"""
import pytest
from app.detection.detector import ObjectDetector

def test_items_catalog_structure():
    """Verifica que el catálogo de clases contenga tuplas válidas (en, es, categoria)."""
    assert len(ObjectDetector.ITEMS_CATALOG) > 30
    for item in ObjectDetector.ITEMS_CATALOG:
        assert len(item) == 3
        en_name, es_name, category = item
        assert isinstance(en_name, str)
        assert isinstance(es_name, str)
        assert category in ["person", "animal", "vehicle", "device", "furniture", "item", "other"]

def test_spanish_translations():
    """Verifica traducciones clave en español de objetos cotidianos."""
    sample_classes = {item[0]: item[1] for item in ObjectDetector.ITEMS_CATALOG}
    assert sample_classes.get("person") == "Persona"
    assert sample_classes.get("cell phone") == "Celular"
    assert sample_classes.get("laptop") == "Computador / Laptop"
    assert sample_classes.get("backpack") == "Mochila"
    assert sample_classes.get("pen") == "Lapicero"
    assert sample_classes.get("dog") == "Perro"
