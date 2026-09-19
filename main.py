"""
NEXUS VISION — Sistema de Cámara Inteligente con IA
Servidor Web FastAPI y Dashboard de Control en Tiempo Real.
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from app.core.config import settings
from app.database.database import init_db
from app.services.vision_service import VisionService
from app.api.routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
SNAPSHOTS_DIR = BASE_DIR / "storage" / "snapshots"

# Asegurar directorios
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: inicializa BD y VisionService al arrancar."""
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} — v{settings.VERSION}")
    print("=" * 60)
    
    # 1. Inicializar Base de Datos SQLite
    init_db()

    # 2. Iniciar Servicio Central de Visión e IA en segundo plano
    vision_service = VisionService.get_instance()
    vision_service.start()

    print(f"🌐 Dashboard Web disponible en: http://localhost:{settings.PORT}")
    print(f"📹 Streaming en vivo activo en: http://localhost:{settings.PORT}/video_feed")
    print("=" * 60)

    yield

    # Al apagar el servidor
    vision_service.stop()

# Crear Aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# 1. Incluir Rutas de API y Streaming
app.include_router(api_router)

# 2. Servir capturas guardadas en /snapshots/...
app.mount("/snapshots", StaticFiles(directory=str(SNAPSHOTS_DIR)), name="snapshots")

# 3. Servir archivos estáticos del frontend (CSS, JS)
@app.get("/styles.css")
def get_css():
    return FileResponse(FRONTEND_DIR / "styles.css")

@app.get("/app.js")
def get_js():
    return FileResponse(FRONTEND_DIR / "app.js")

@app.get("/")
def get_dashboard():
    """Ruta principal: sirve el Dashboard HTML."""
    return FileResponse(FRONTEND_DIR / "index.html")

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )
