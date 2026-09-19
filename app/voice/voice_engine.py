"""
Motor de Síntesis de Voz en Español para NEXUS VISION.
Emite alertas y respuestas habladas de forma asíncrona mediante hilos para no congelar la cámara.
"""
import time
import queue
import threading
from typing import Optional
import pyttsx3

class VoiceEngine:
    """Administra la reproducción de voz sin bloquear el hilo principal."""

    _instance: Optional['VoiceEngine'] = None

    @classmethod
    def get_instance(cls) -> 'VoiceEngine':
        if cls._instance is None:
            cls._instance = VoiceEngine()
        return cls._instance

    def __init__(self):
        self.speech_queue = queue.Queue()
        self.is_running = True
        self.enabled = True

        # Iniciar hilo de procesamiento de voz en segundo plano
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()

    def _speech_worker(self):
        """Hilo trabajador que inicializa el motor TTS de Windows y consume la cola de voz."""
        try:
            engine = pyttsx3.init()
            # Ajustar velocidad y volumen
            engine.setProperty('rate', 165)
            engine.setProperty('volume', 0.95)

            # Intentar seleccionar una voz en español disponible en Windows
            voices = engine.getProperty('voices')
            for v in voices:
                if "spanish" in v.name.lower() or "helena" in v.name.lower() or "sabina" in v.name.lower() or "mexico" in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
        except Exception as e:
            print(f"⚠️ Nota de inicialización de audio pyttsx3: {e}")
            return

        while self.is_running:
            try:
                text = self.speech_queue.get(timeout=0.5)
                if text and self.enabled:
                    engine.say(text)
                    engine.runAndWait()
                self.speech_queue.task_done()
            except queue.Empty:
                continue
            except Exception as err:
                print(f"⚠️ Error reproduciendo voz: {err}")

    def speak(self, text: str):
        """Agrega una frase a la cola de voz para ser leída en segundo plano."""
        if not self.enabled or not text:
            return
        # Limpiar texto de caracteres especiales
        clean_text = text.replace("*", "").replace("`", "").replace("🚨", "").replace("📸", "").replace("👁️", "")
        self.speech_queue.put(clean_text)

    def stop(self):
        self.is_running = False
