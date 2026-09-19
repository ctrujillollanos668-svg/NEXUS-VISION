# ==============================================================================
# NEXUS VISION — Dockerfile para Despliegue en Contenedor
# ==============================================================================
FROM python:3.10-slim

# Evitar que Python escriba archivos .pyc y forzar salida de consola inmediata
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema requeridas por OpenCV y audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    espeak \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente de NEXUS VISION
COPY . .

# Crear directorios de almacenamiento si no existen
RUN mkdir -p storage/snapshots models

# Exponer el puerto del Dashboard y API
EXPOSE 8000

# Comando de inicio del servidor
CMD ["python", "main.py"]
