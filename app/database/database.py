"""
Configuración de la Base de Datos SQLite con SQLAlchemy.
Permite persistir eventos, detecciones y metadatos de capturas.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "nexus_vision.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Crear motor de base de datos
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Crea todas las tablas en la base de datos si no existen."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"🗄️ Base de datos SQLite inicializada en: {DB_PATH}")
