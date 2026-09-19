/**
 * NEXUS VISION — Controlador Frontend del Dashboard
 * Soporte de Voz Bidireccional y Respuestas Instantáneas.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const liveClock = document.getElementById('liveClock');
    const systemStatusText = document.getElementById('systemStatusText');
    const globalAlertBanner = document.getElementById('globalAlertBanner');
    const globalAlertText = document.getElementById('globalAlertText');

    const activeCamTitle = document.getElementById('activeCamTitle');
    const cameraSelect = document.getElementById('cameraSelect');
    const btnScanCams = document.getElementById('btnScanCams');

    const fpsVal = document.getElementById('fpsVal');
    const inferVal = document.getElementById('inferVal');
    const motionVal = document.getElementById('motionVal');
    const deviceVal = document.getElementById('deviceVal');
    const statPersons = document.getElementById('statPersons');
    const statDevices = document.getElementById('statDevices');
    const statItems = document.getElementById('statItems');
    const statAlerts = document.getElementById('statAlerts');
    const totalItemsCount = document.getElementById('totalItemsCount');
    const inventoryContainer = document.getElementById('inventoryContainer');

    const btnToggleMotion = document.getElementById('btnToggleMotion');
    const motionBtnText = document.getElementById('motionBtnText');
    const btnToggleZones = document.getElementById('btnToggleZones');
    const zonesBtnText = document.getElementById('zonesBtnText');
    const btnToggleVoiceTTS = document.getElementById('btnToggleVoiceTTS');
    const voiceTTSBtnText = document.getElementById('voiceTTSBtnText');
    const btnRefresh = document.getElementById('btnRefresh');
    const btnReloadEvents = document.getElementById('btnReloadEvents');

    const eventsGallery = document.getElementById('eventsGallery');
    const videoFeed = document.getElementById('videoFeed');

    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalInfo = document.getElementById('modalInfo');
    const modalClose = document.getElementById('modalClose');

    // Elementos de Chat con IA y Voz
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chipButtons = document.querySelectorAll('.chip-btn');
    const btnMic = document.getElementById('btnMic');
    const micIcon = document.getElementById('micIcon');

    let voiceOutputEnabled = true;
    let recognition = null;
    let isListening = false;

    // 1. Reloj en Vivo
    function updateClock() {
        const now = new Date();
        liveClock.textContent = now.toLocaleTimeString('es-CO', { hour12: false });
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. Reconocimiento de Voz
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isListening = true;
            btnMic.classList.add('listening');
            micIcon.textContent = '🔴';
            chatInput.placeholder = 'Escuchando tu voz... habla ahora';
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            sendChatMessage(transcript);
        };

        recognition.onerror = (event) => {
            console.warn('Error reconocimiento voz:', event.error);
            stopListening();
        };

        recognition.onend = () => {
            stopListening();
        };
    } else {
        btnMic.style.display = 'none';
    }

    function stopListening() {
        isListening = false;
        btnMic.classList.remove('listening');
        micIcon.textContent = '🎙️';
        chatInput.placeholder = 'Háblame con el micrófono o escribe aquí...';
    }

    btnMic.addEventListener('click', () => {
        if (!recognition) return;
        if (isListening) {
            recognition.stop();
        } else {
            try {
                recognition.start();
            } catch (err) {
                recognition.stop();
            }
        }
    });

    // 3. Síntesis de Voz
    let currentUtterance = null;
    function speakText(text) {
        if (!voiceOutputEnabled || !('speechSynthesis' in window)) return;

        window.speechSynthesis.cancel();

        const clean = text
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/#/g, '')
            .replace(/[-_]/g, ' ')
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
            .replace(/[\u{2600}-\u{26FF}]/gu, '')
            .replace(/[\u{2700}-\u{27BF}]/gu, '')
            .trim();

        if (!clean) return;

        currentUtterance = new SpeechSynthesisUtterance(clean);
        currentUtterance.lang = 'es-ES';
        currentUtterance.rate = 1.05;

        const voices = window.speechSynthesis.getVoices();
        const esVoice = voices.find(v => v.lang.startsWith('es') || v.lang.includes('es-'));
        if (esVoice) {
            currentUtterance.voice = esVoice;
        }

        currentUtterance.onend = () => {
            currentUtterance = null;
        };

        window.speechSynthesis.speak(currentUtterance);
    }

    btnToggleVoiceTTS.addEventListener('click', () => {
        voiceOutputEnabled = !voiceOutputEnabled;
        if (voiceOutputEnabled) {
            voiceTTSBtnText.textContent = "Voz de Nexus (ON)";
            btnToggleVoiceTTS.className = "btn btn-secondary";
            speakText("Voz activada.");
        } else {
            voiceTTSBtnText.textContent = "Voz de Nexus (OFF)";
            btnToggleVoiceTTS.className = "btn btn-outline";
            window.speechSynthesis.cancel();
        }
    });

    // 4. Métricas en Vivo (/api/stats)
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();

            systemStatusText.textContent = data.status;
            fpsVal.textContent = data.fps.toFixed(1);
            if (inferVal && data.inference_ms !== undefined) inferVal.textContent = data.inference_ms.toFixed(1);
            if (deviceVal && data.device_name) deviceVal.textContent = data.device_name.startsWith('GPU') ? '⚡ GPU' : 'CPU';
            motionVal.textContent = `${data.scene_motion.toFixed(1)}%`;

            statPersons.textContent = data.categories.person || 0;
            statDevices.textContent = data.categories.device || 0;
            statItems.textContent = data.categories.item || 0;
            totalItemsCount.textContent = data.total_items_in_scene || 0;

            if (data.only_moving) {
                motionBtnText.textContent = "Filtro: Solo Movimiento (ON)";
                btnToggleMotion.className = "btn btn-primary";
            } else {
                motionBtnText.textContent = "Filtro: Todos los Objetos (OFF)";
                btnToggleMotion.className = "btn btn-secondary";
            }

            if (data.zones_enabled) {
                zonesBtnText.textContent = "Zona Restringida (ON)";
                btnToggleZones.className = "btn btn-secondary";
            } else {
                zonesBtnText.textContent = "Zona Restringida (OFF)";
                btnToggleZones.className = "btn btn-outline";
            }

            if (data.active_alert) {
                globalAlertText.textContent = data.active_alert;
                globalAlertBanner.classList.add('active');
            } else {
                globalAlertBanner.classList.remove('active');
            }

            renderInventory(data.inventory);

        } catch (err) {
            systemStatusText.textContent = "DESCONECTADO";
        }
    }

    function renderInventory(inventory) {
        if (!inventory || Object.keys(inventory).length === 0) {
            inventoryContainer.innerHTML = `<div class="empty-state">No hay objetos detectados en este momento.</div>`;
            return;
        }

        let html = '';
        for (const [name, qty] of Object.entries(inventory)) {
            html += `
                <div class="tag-item">
                    <span>${name}</span>
                    <span class="tag-count">${qty}</span>
                </div>
            `;
        }
        inventoryContainer.innerHTML = html;
    }

    // 5. Historial de Eventos (/api/events)
    async function fetchEvents() {
        try {
            const res = await fetch('/api/events');
            if (!res.ok) return;
            const events = await res.json();

            const alertCount = events.filter(e => e.alert_level === 'ALERT').length;
            statAlerts.textContent = alertCount;

            if (events.length === 0) {
                eventsGallery.innerHTML = `<div class="empty-state">No hay eventos registrados en la base de datos aún.</div>`;
                return;
            }

            let html = '';
            events.forEach(e => {
                const isAlert = e.alert_level === 'ALERT';
                const cardClass = isAlert ? 'event-card alert-card' : 'event-card';
                const badgeClass = isAlert ? 'event-badge alert' : 'event-badge info';
                const badgeText = isAlert ? '🚨 ALERTA' : '📸 REGISTRO';
                const thumbUrl = e.snapshot_url || '/placeholder.jpg';

                html += `
                    <div class="${cardClass}" onclick="openSnapshotModal('${thumbUrl}', '${e.description}', '${e.date} ${e.time}')">
                        <div class="event-thumb-wrap">
                            <img src="${thumbUrl}" alt="${e.object_name}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'120\\' viewBox=\\'0 0 200 120\\'><rect fill=\\'%23111\\' width=\\'200\\' height=\\'120\\'/><text fill=\\'%23555\\' x=\\'50%\\' y=\\'50%\\' text-anchor=\\'middle\\'>Captura</text></svg>'">
                            <span class="${badgeClass}">${badgeText}</span>
                        </div>
                        <div class="event-card-body">
                            <div class="event-object-title">${e.object_name} (${e.confidence}%)</div>
                            <div class="event-meta">
                                <span>${e.zone_name || 'Cámara Principal'}</span>
                                <span>${e.time}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            eventsGallery.innerHTML = html;

        } catch (err) {
            console.error("Error cargando historial de eventos:", err);
        }
    }

    // 6. Chat con IA Rápido con Indicador de Pensando
    async function sendChatMessage(msg) {
        if (!msg || msg.trim() === '') return;

        appendChatBubble('user', 'Tú', msg);
        chatInput.value = '';

        // Burbuja de "pensando..."
        const loadingBubbleId = 'loading-' + Date.now();
        const loadingBubble = document.createElement('div');
        loadingBubble.id = loadingBubbleId;
        loadingBubble.className = 'chat-bubble ai';
        loadingBubble.innerHTML = `<div class="bubble-sender">🤖 Nexus AI</div><div class="bubble-text"><em>Observando la cámara y pensando... 💭</em></div>`;
        chatMessages.appendChild(loadingBubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });

            // Remover burbuja de carga
            const el = document.getElementById(loadingBubbleId);
            if (el) el.remove();

            if (res.ok) {
                const data = await res.json();
                let formatted = data.reply
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/\n/g, '<br>');
                appendChatBubble('ai', '🤖 Nexus AI', formatted, true);

                speakText(data.reply);

            } else {
                appendChatBubble('ai', '🤖 Nexus AI', 'Lo siento, ocurrió un error procesando tu consulta.');
            }
        } catch (err) {
            const el = document.getElementById(loadingBubbleId);
            if (el) el.remove();
            appendChatBubble('ai', '🤖 Nexus AI', 'Error de conexión con el servidor.');
        }
    }

    function appendChatBubble(type, sender, text, isHtml = false) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${type}`;

        const senderEl = document.createElement('div');
        senderEl.className = 'bubble-sender';
        senderEl.textContent = sender;

        const textEl = document.createElement('div');
        textEl.className = 'bubble-text';
        if (isHtml) {
            textEl.innerHTML = text;
        } else {
            textEl.textContent = text;
        }

        bubble.appendChild(senderEl);
        bubble.appendChild(textEl);
        chatMessages.appendChild(bubble);

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        sendChatMessage(chatInput.value);
    });

    chipButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt');
            sendChatMessage(prompt);
        });
    });

    // 7. Modal de Capturas
    window.openSnapshotModal = function(url, desc, time) {
        modalImage.src = url;
        modalInfo.textContent = `${desc} — [${time}]`;
        imageModal.classList.add('active');
    };

    modalClose.addEventListener('click', () => {
        imageModal.classList.remove('active');
    });

    imageModal.addEventListener('click', (e) => {
        if (e.target === imageModal) {
            imageModal.classList.remove('active');
        }
    });

    // 8. Gestión de Múltiples Cámaras
    async function loadCameras() {
        try {
            const res = await fetch('/api/cameras');
            if (!res.ok) return;
            const data = await res.json();
            
            cameraSelect.innerHTML = '';
            data.cameras.forEach(cam => {
                const opt = document.createElement('option');
                opt.value = cam.id;
                opt.textContent = cam.name;
                if (cam.id == data.current_camera) {
                    opt.selected = true;
                }
                cameraSelect.appendChild(opt);
            });

            activeCamTitle.textContent = `TRANSMISIÓN EN TIEMPO REAL (CÁMARA ${data.current_camera})`;
        } catch (err) {
            console.error("Error cargando cámaras:", err);
        }
    }

    cameraSelect.addEventListener('change', async (e) => {
        const newCamId = e.target.value;
        try {
            const res = await fetch('/api/cameras/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_id: newCamId })
            });
            const data = await res.json();
            if (data.success) {
                activeCamTitle.textContent = `TRANSMISIÓN EN TIEMPO REAL (CÁMARA ${newCamId})`;
                videoFeed.src = "/video_feed?t=" + new Date().getTime();
                speakText(`Cámara cambiada a la fuente ${newCamId}.`);
            } else {
                alert(`No se pudo conectar a la cámara ${newCamId}.`);
                loadCameras();
            }
        } catch (err) {
            alert("Error al intentar cambiar de cámara.");
        }
    });

    btnScanCams.addEventListener('click', async () => {
        btnScanCams.disabled = true;
        btnScanCams.innerHTML = '<span>⏳ Escaneando...</span>';
        await loadCameras();
        btnScanCams.disabled = false;
        btnScanCams.innerHTML = '<span>🔍 Escanear</span>';
    });

    // 9. Botones de Control
    btnToggleMotion.addEventListener('click', async () => {
        await fetch('/api/toggle_motion', { method: 'POST' });
        fetchStats();
    });

    btnToggleZones.addEventListener('click', async () => {
        await fetch('/api/toggle_zones', { method: 'POST' });
        fetchStats();
    });

    btnRefresh.addEventListener('click', () => {
        videoFeed.src = "/video_feed?t=" + new Date().getTime();
    });

    btnReloadEvents.addEventListener('click', () => {
        fetchEvents();
    });

    // Intervalos y Carga Inicial
    setInterval(fetchStats, 1500);
    setInterval(fetchEvents, 4000);

    loadCameras();
    fetchStats();
    fetchEvents();
});
