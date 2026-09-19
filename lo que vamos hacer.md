# NEXUS VISION — Sistema de Cámara Inteligente con IA

## 1. Objetivo del proyecto

Quiero desarrollar un software llamado **NEXUS VISION**, construido principalmente con **Python**, que utilice una cámara/webcam y visión artificial mediante IA para analizar en tiempo real lo que está viendo.

El sistema debe ser capaz de detectar diferentes tipos de objetos, personas, animales y vehículos, mostrar las detecciones visualmente y generar eventos y alertas cuando se cumplan determinadas condiciones.

Quiero que sea un proyecto grande, profesional y escalable, construido desde cero y por etapas.

**No quiero un simple ejemplo de cámara. Quiero construir un software completo.**

---

# 2. Funcionalidades principales

## Cámara

El sistema debe permitir:

* Utilizar una webcam conectada al computador.
* Mostrar el video en tiempo real.
* Permitir seleccionar/configurar la cámara.
* Mostrar FPS.
* Mostrar el estado de la cámara.
* Permitir iniciar y detener la cámara.
* Preparar la arquitectura para soportar varias cámaras posteriormente.

---

# 3. Detección mediante IA

La cámara debe analizar cada frame utilizando un modelo de visión artificial.

Debe poder detectar inicialmente:

* Personas
* Perros
* Gatos
* Aves
* Vehículos
* Motocicletas
* Bicicletas
* Celulares
* Mochilas
* Bolsos
* Computadores
* Sillas
* Mesas
* Puertas
* Otros objetos que soporte el modelo utilizado.

Para cada detección quiero obtener como mínimo:

```text
Objeto:
Confianza:
Posición:
Bounding Box:
Fecha:
Hora:
Cámara:
```

Ejemplo:

```text
PERSONA
Confianza: 94%
Posición: X=350 Y=120
Hora: 21:42:15
```

---

# 4. Visualización de detecciones

Quiero que el sistema dibuje automáticamente un rectángulo alrededor de cada objeto detectado.

Ejemplo:

```text
┌────────────────────────────────────┐
│                                    │
│        ┌──────────────┐            │
│        │ PERSONA 94%  │            │
│        │              │            │
│        │              │            │
│        └──────────────┘            │
│                                    │
│                    ┌────────────┐  │
│                    │ CELULAR 87%│  │
│                    └────────────┘  │
│                                    │
└────────────────────────────────────┘
```

También quiero mostrar:

```text
Personas: 2
Animales: 1
Vehículos: 0
Objetos: 4
```

---

# 5. Sistema de eventos

Cada vez que ocurra algo importante, el sistema debe generar un evento.

Ejemplos:

```text
PERSONA_DETECTADA
ANIMAL_DETECTADO
VEHICULO_DETECTADO
OBJETO_DETECTADO
PERSONA_ENTRA_ZONA
PERSONA_SALE_ZONA
MOVIMIENTO_DETECTADO
```

Cada evento debe guardar:

```text
ID
Tipo de evento
Fecha
Hora
Cámara
Objeto detectado
Confianza
Imagen/captura
Descripción
```

---

# 6. Sistema de zonas

Quiero poder crear zonas dentro de la imagen.

Por ejemplo:

```text
┌──────────────────────────────────┐
│                                  │
│             CASA                 │
│                                  │
│                    ┌──────────┐  │
│                    │          │  │
│                    │ ZONA     │  │
│                    │RESTRING. │  │
│                    │          │  │
│                    └──────────┘  │
│                                  │
└──────────────────────────────────┘
```

El usuario debe poder configurar zonas como:

* Zona restringida
* Entrada
* Salida
* Parqueadero
* Almacén
* Oficina
* Patio
* Cualquier zona personalizada

La zona debe poder configurarse desde el panel.

---

# 7. Reglas inteligentes

Quiero un sistema de reglas.

Ejemplos:

```text
SI detecta PERSONA
ENTONCES crear evento
```

```text
SI detecta PERSONA dentro de ZONA_RESTRINGIDA
ENTONCES generar ALERTA
```

```text
SI detecta VEHICULO
ENTONCES registrar evento
```

```text
SI detecta ANIMAL
ENTONCES registrar evento
```

Quiero que posteriormente las reglas puedan configurarse desde la interfaz.

---

# 8. Alertas

Cuando se cumpla una regla, el sistema debe generar una alerta.

Ejemplo:

```text
🚨 ALERTA

Se detectó una persona
en la zona restringida.

Fecha: 18/09/2026
Hora: 21:45:32
Cámara: Cámara 1
```

Las alertas pueden incluir:

* Notificación dentro del sistema.
* Sonido.
* Captura de pantalla.
* Registro en la base de datos.

Posteriormente se pueden agregar otros métodos de notificación.

---

# 9. Capturas

Cuando ocurra un evento importante, quiero poder guardar una captura.

Ejemplo:

```text
events/
    2026/
        09/
            18/
                event_001.jpg
                event_002.jpg
                event_003.jpg
```

La base de datos debe almacenar la ubicación de la captura.

---

# 10. Historial

Quiero una sección donde pueda consultar todos los eventos.

Ejemplo:

```text
HISTORIAL

21:42:15
👤 Persona detectada

21:43:02
🐕 Animal detectado

21:45:32
🚨 Persona entró a zona restringida

21:47:10
🚗 Vehículo detectado
```

Debe permitir filtros por:

* Fecha
* Hora
* Tipo de evento
* Cámara
* Objeto
* Nivel de alerta

---

# 11. Dashboard

Quiero un dashboard moderno.

Debe mostrar:

```text
Cámaras activas
Personas detectadas
Animales detectados
Vehículos detectados
Objetos detectados
Alertas
Eventos recientes
```

También quiero gráficos estadísticos.

Ejemplo:

```text
EVENTOS DE HOY

Personas       ███████████
Animales       ████
Vehículos      ██████
Alertas        ██
```

---

# 12. IA generativa

Además de la detección de objetos, quiero integrar posteriormente una IA capaz de interpretar la escena.

Por ejemplo:

Usuario:

> ¿Qué está viendo la cámara?

IA:

> Se observa una persona frente a un escritorio. También se detecta un computador y una mochila.

Otro ejemplo:

Usuario:

> ¿Qué ocurrió recientemente?

IA:

> Hace aproximadamente dos minutos se detectó una persona entrando en la zona configurada como restringida.

La IA generativa debe trabajar junto con el sistema de detección.

---

# 13. Voz

Posteriormente quiero agregar reconocimiento de voz y síntesis de voz.

Ejemplo:

Usuario:

> "Nexus, ¿qué está pasando?"

Sistema:

> "Actualmente hay una persona y un vehículo detectados."

También quiero que el sistema pueda emitir alertas por voz:

> "Alerta. Se detectó una persona en la zona restringida."

---

# 14. Base de datos

Utilizar inicialmente SQLite para facilitar el desarrollo.

La arquitectura debe permitir migrar posteriormente a PostgreSQL.

Crear tablas para:

```text
users
cameras
zones
detections
events
alerts
rules
snapshots
settings
```

Diseñar correctamente las relaciones entre las tablas.

---

# 15. Arquitectura

Quiero una arquitectura limpia y organizada.

Una estructura inicial podría ser:

```text
nexus-vision/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── detection/
│   ├── camera/
│   ├── events/
│   ├── alerts/
│   ├── zones/
│   ├── rules/
│   ├── ai/
│   ├── database/
│   └── services/
│
├── frontend/
│
├── models/
│
├── storage/
│   ├── snapshots/
│   └── recordings/
│
├── tests/
│
├── scripts/
│
├── requirements.txt
├── .env.example
├── README.md
└── main.py
```

Puedes modificar esta estructura si existe una arquitectura mejor, pero debes explicarme por qué.

---

# 16. Tecnologías

Quiero utilizar principalmente:

### Backend

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* SQLite inicialmente
* PostgreSQL posteriormente

### Visión artificial

* OpenCV
* Un modelo moderno de detección de objetos compatible con Python

### IA

Quiero dejar preparada la arquitectura para utilizar:

* Ollama
* Modelos locales
* Modelos de visión
* Modelos de lenguaje

### Frontend

Puedes utilizar:

* HTML
* CSS
* JavaScript

o una tecnología frontend adecuada si existe una razón clara para utilizarla.

---

# 17. Rendimiento

El sistema debe estar diseñado pensando en video en tiempo real.

Quiero evitar:

* Procesar innecesariamente todos los frames.
* Bloquear la interfaz.
* Crear múltiples procesos innecesarios.
* Consumir memoria excesivamente.

Explica cómo podemos optimizar:

* FPS
* Inferencia
* CPU
* GPU
* RAM
* procesamiento de frames

Si existe soporte para GPU, explica cómo aprovecharlo sin hacer que el proyecto dependa obligatoriamente de una GPU.

---

# 18. Seguridad y privacidad

El proyecto debe utilizarse únicamente con cámaras y espacios donde tengamos autorización.

No quiero que el sistema intente identificar personas desconocidas ni obtener información personal de ellas desde Internet.

El sistema debe enfocarse en:

* Detección de objetos.
* Detección de movimiento.
* Eventos.
* Alertas.
* Seguridad del espacio autorizado.

Si posteriormente se implementa reconocimiento de personas registradas, debe limitarse a usuarios autorizados y explicarse claramente cómo proteger esos datos.

---

# 19. Desarrollo por etapas

MUY IMPORTANTE:

**NO quiero que generes todo el proyecto de una sola vez.**

Quiero construirlo paso a paso y aprender mientras lo hacemos.

### FASE 1

Preparar:

```text
Python
Entorno virtual
Estructura del proyecto
Dependencias
```

### FASE 2

Conectar webcam:

```text
Python
↓
OpenCV
↓
Video en tiempo real
```

### FASE 3

Agregar detección de objetos:

```text
Cámara
↓
OpenCV
↓
Modelo IA
↓
Detecciones
```

### FASE 4

Agregar bounding boxes y contadores.

### FASE 5

Crear sistema de eventos.

### FASE 6

Guardar capturas y eventos en SQLite.

### FASE 7

Crear zonas.

### FASE 8

Crear reglas y alertas.

### FASE 9

Crear dashboard web.

### FASE 10

Agregar IA generativa.

### FASE 11

Agregar voz.

### FASE 12

Agregar múltiples cámaras.

### FASE 13

Optimización.

### FASE 14

Tests.

### FASE 15

Docker.

### FASE 16

Empaquetar el programa para Windows.

---

# 20. Cómo quiero que me enseñes

Soy estudiante y quiero **entender el proyecto**, no simplemente copiar y pegar.

Por cada etapa:

1. Explícame qué vamos a construir.
2. Explícame qué tecnología utilizaremos.
3. Muéstrame la estructura de carpetas.
4. Dame los comandos exactos para Windows.
5. Dame el código completo de esa etapa.
6. Explícame el código de manera sencilla.
7. Dime dónde colocar cada archivo.
8. Dime cómo ejecutarlo.
9. Dime qué resultado debería aparecer.
10. Si aparece un error, ayúdame a solucionarlo antes de continuar.

No avances a la siguiente fase hasta que la fase actual funcione.

---

# 21. Reglas importantes

No inventes archivos, funciones o configuraciones que no existan.

No me des código incompleto si la etapa requiere varios archivos.

Cuando cambies un archivo, indícame exactamente:

```text
ARCHIVO:
ruta/del/archivo.py
```

y proporciona el contenido completo cuando sea necesario.

No destruyas funcionalidades que ya funcionan.

Mantén una arquitectura limpia y preparada para crecer.

Prioriza código entendible para un estudiante.

---

# 22. Objetivo final

Al terminar quiero tener un software llamado:

# NEXUS VISION

Que permita:

```text
📷 Cámara
   ↓
👁️ Visión artificial
   ↓
🎯 Detección de objetos
   ↓
👤 Personas
🐕 Animales
🚗 Vehículos
📦 Objetos
   ↓
🧠 Reglas
   ↓
🚨 Alertas
   ↓
📸 Capturas
   ↓
🗄️ Historial
   ↓
📊 Dashboard
   ↓
🤖 IA generativa
   ↓
🎤 Voz
```

Quiero que el resultado final sea un proyecto profesional, modular, escalable y educativo, construido progresivamente con Python.

## PRIMER PASO

Comienza únicamente con la **FASE 1**.

No desarrolles todavía el detector de objetos.

Primero explícame qué vamos a instalar, cómo crear el entorno virtual y cómo organizar la estructura inicial del proyecto.
