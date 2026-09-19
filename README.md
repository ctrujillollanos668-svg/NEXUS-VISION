# 👁️ NEXUS VISION — Sistema Inteligente de Cámara y Vigilancia con IA

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![YOLO-World](https://img.shields.io/badge/YOLO--World-v2-green.svg)](https://docs.ultralytics.com/models/yolo-world/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-Multimodal%20Vision-purple.svg)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

**NEXUS VISION** es una plataforma profesional y modular de videovigilancia, visión artificial e inteligencia artificial multimodal construida en Python. Integra detección de objetos de vocabulario abierto en español, filtrado inteligente de movimiento, zonas de seguridad restringidas con alarmas sonoras, base de datos SQLite con capturas automáticas, dashboard web táctico en tiempo real y un Asistente Generativo multimodal con voz bidireccional conectado a **Google Gemini**.

---

## 🚀 Características Principales

1. **📹 Captura y Transmisión en Vivo:**
   - Transmisión continua MJPEG de baja latencia a 30 FPS optimizada para navegadores web modernos.
   - Detección y escaneo de cámaras físicas y soporte para múltiples fuentes de video.
2. **🎯 Detección de Objetos Universal (YOLO-World v2):**
   - Reconocimiento de 51+ clases en español (personas, celulares, laptops, mochilas, útiles de papelería, gafas, tazas, llaves, vehículos, etc.), incluso sostenidos en la mano o superpuestos.
3. **⚡ Filtro Inteligente de Movimiento (MOG2):**
   - Ignora objetos estáticos o de fondo y resalta únicamente los elementos en movimiento en la sala.
4. **🛡️ Zonas de Seguridad y Reglas de Intrusión:**
   - Creación de zonas restringidas visuales con alarma sonora (`winsound.Beep`), indicador de alerta táctico y captura automática de evidencia fotográfica con cooldown de 15 segundos.
5. **🗄️ Base de Datos e Historial de Capturas:**
   - Persistencia completa con SQLAlchemy y SQLite (`storage/nexus_vision.db`).
   - Galería de imágenes modal interactiva con visor ampliado.
6. **🤖 Asistente de IA Generativa con Visión Multimodal (Gemini):**
   - Envía el fotograma en vivo comprimido a 512px para respuestas instantáneas en menos de un segundo sobre lo que está ocurriendo frente a la cámara.
7. **🎙️ Voz Bidireccional:**
   - Reconocimiento de voz mediante micrófono con Web Speech API y síntesis de voz hablada en español.
8. **📊 Dashboard Ciber-Táctico:**
   - Interfaz gráfica oscura con telemetría en vivo de FPS, milisegundos de inferencia (`⚡ ms`), aceleración por hardware (GPU/CPU) y contador de inventario de sala.

---

## 📁 Estructura del Proyecto

```text
nexus-vision/
├── app/
│   ├── ai/               # Asistente Generativo Multimodal (Google Gemini)
│   ├── alerts/           # Gestor de alertas sonoras y capturas
│   ├── api/              # Endpoints REST y streaming MJPEG
│   ├── camera/           # Captura OpenCV, cálculo FPS, HUD táctico y multi-cámara
│   ├── core/             # Configuración central y variables de entorno (Pydantic Settings)
│   ├── database/         # Modelos de base de datos SQLAlchemy y SQLite
│   ├── detection/        # Inferencia YOLO-World v2 y filtro de movimiento MOG2
│   ├── events/           # Registro de eventos y guardado de capturas
│   ├── services/         # Servicio central de visión artificial (VisionService)
│   ├── voice/            # Motor de síntesis de voz offline (pyttsx3)
│   └── zones/            # Gestor de zonas de seguridad y cálculo de intrusiones
├── frontend/             # Dashboard Web (HTML5, CSS3 Glassmorphism, JS)
├── models/               # Pesos de los modelos de visión artificial (.pt)
├── storage/              # Base de datos SQLite y capturas de seguridad organizadas por fecha
├── tests/                # Suite de 16 pruebas automatizadas con pytest
├── .dockerignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── main.py               # Punto de entrada y servidor FastAPI
├── nexus_vision.spec     # Especificación para compilación de ejecutable .exe
├── requirements.txt      # Dependencias del proyecto
└── run_nexus_vision.bat  # Lanzador de un solo clic para Windows
```

---

## 🛠️ Instalación y Puesta en Marcha (Windows)

### Opción 1: Lanzador de un Solo Clic
Haz doble clic sobre el archivo:
```bat
run_nexus_vision.bat
```

### Opción 2: Ejecución Manual en Terminal

1. **Clonar el repositorio:**
   ```powershell
   git clone https://github.com/ctrujillollanos668-svg/NEXUS-VISION.git
   cd NEXUS-VISION
   ```

2. **Crear y activar el entorno virtual:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno (`.env`):**
   Copia el archivo de ejemplo y coloca tu API Key de Google Gemini:
   ```powershell
   cp .env.example .env
   ```

5. **Iniciar el servidor:**
   ```powershell
   python main.py
   ```

6. **Abrir el Dashboard en el navegador:**
   Ingresa a [http://localhost:8000](http://localhost:8000).

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto incluye 16 pruebas unitarias y de integración que validan la API, la cámara, el detector, la base de datos y las zonas:

```powershell
.\.venv\Scripts\pytest.exe -v
```

---

## 🐳 Despliegue con Docker

Para construir y levantar la aplicación en un contenedor Docker:

```bash
docker-compose up --build -d
```

---

## 📜 Roadmap de Desarrollo (16 Fases Completadas)

- [x] **Fase 1:** Configuración del entorno virtual, arquitectura base y dependencias.
- [x] **Fase 2:** Conexión de webcam, control de FPS y HUD táctico en pantalla.
- [x] **Fase 3 & 4:** Detección de objetos con IA YOLO-World (51+ clases en español) y conteo en capas.
- [x] **Fase 5 & 6:** Filtro de movimiento MOG2, base de datos SQLite y capturas organizadas por fecha.
- [x] **Fase 7 & 8:** Zonas de seguridad restringidas, reglas de intrusión y alertas sonoras.
- [x] **Fase 9:** Dashboard web ciber-táctico en tiempo real con streaming MJPEG.
- [x] **Fase 10:** Asistente generativo multimodal con Google Gemini y visión de cámara en vivo.
- [x] **Fase 11:** Voz bidireccional (reconocimiento con micrófono y síntesis hablada).
- [x] **Fase 12:** Soporte multi-cámara y conmutación de fuentes de video en caliente.
- [x] **Fase 13:** Optimización de rendimiento, telemetría de inferencia en ms y aceleración GPU/CPU.
- [x] **Fase 14:** Suite completa de 16 pruebas automatizadas con `pytest`.
- [x] **Fase 15:** Contenedorización con `Dockerfile` y `docker-compose.yml`.
- [x] **Fase 16:** Lanzador interactivo `.bat` y empaquetado para Windows con PyInstaller.

---

## 👤 Autor
Desarrollado como proyecto de visión artificial e inteligencia artificial aplicada.
Repositorio oficial: [https://github.com/ctrujillollanos668-svg/NEXUS-VISION](https://github.com/ctrujillollanos668-svg/NEXUS-VISION)
