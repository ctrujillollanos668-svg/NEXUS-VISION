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
    const connectedDevicesCount = document.getElementById('connectedDevicesCount');
    const devicesListContainer = document.getElementById('devicesListContainer');

    const btnToggleAutoSnapshot = document.getElementById('btnToggleAutoSnapshot');
    const autoSnapshotBtnText = document.getElementById('autoSnapshotBtnText');
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

            if (btnToggleAutoSnapshot && autoSnapshotBtnText) {
                if (data.auto_snapshot) {
                    autoSnapshotBtnText.textContent = "Foto Automática (ON)";
                    btnToggleAutoSnapshot.className = "btn btn-primary";
                } else {
                    autoSnapshotBtnText.textContent = "Foto Automática (OFF)";
                    btnToggleAutoSnapshot.className = "btn btn-outline";
                }
            }

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

    // 5. Historial de Eventos (/api/events) con Filtro por Cámara
    let currentCameraFilter = 'ALL';
    let cachedEventsList = [];
    const cameraFilterChips = document.getElementById('cameraFilterChips');

    async function fetchEvents() {
        try {
            const res = await fetch('/api/events');
            if (!res.ok) return;
            cachedEventsList = await res.json();

            const alertCount = cachedEventsList.filter(e => e.alert_level === 'ALERT').length;
            statAlerts.textContent = alertCount;

            updateCameraFilterChips(cachedEventsList);
            renderFilteredEvents();

        } catch (err) {
            console.error("Error cargando historial de eventos:", err);
        }
    }

    function updateCameraFilterChips(events) {
        if (!cameraFilterChips) return;
        const camCounts = {};
        events.forEach(e => {
            const name = e.zone_name || 'Webcam Principal';
            camCounts[name] = (camCounts[name] || 0) + 1;
        });

        let chipsHtml = `
            <button class="btn btn-sm ${currentCameraFilter === 'ALL' ? 'btn-primary' : 'btn-outline'}" onclick="setCameraFilter('ALL')" style="padding: 4px 10px; font-size: 0.76rem;">
                Todas (${events.length})
            </button>
        `;

        for (const [camName, count] of Object.entries(camCounts)) {
            const isActive = currentCameraFilter === camName;
            chipsHtml += `
                <button class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline'}" onclick="setCameraFilter('${camName.replace(/'/g, "\\'")}')" style="padding: 4px 10px; font-size: 0.76rem;">
                    📷 ${camName} (${count})
                </button>
            `;
        }

        cameraFilterChips.innerHTML = chipsHtml;
    }

    window.setCameraFilter = function(camName) {
        currentCameraFilter = camName;
        updateCameraFilterChips(cachedEventsList);
        renderFilteredEvents();
    };

    function renderFilteredEvents() {
        const filtered = currentCameraFilter === 'ALL' 
            ? cachedEventsList 
            : cachedEventsList.filter(e => (e.zone_name || 'Webcam Principal') === currentCameraFilter);

        if (filtered.length === 0) {
            eventsGallery.innerHTML = `<div class="empty-state">No hay capturas registradas para esta cámara.</div>`;
            return;
        }

        let html = '';
        filtered.forEach(e => {
            const isAlert = e.alert_level === 'ALERT';
            const cardClass = isAlert ? 'event-card alert-card' : 'event-card';
            const badgeClass = isAlert ? 'event-badge alert' : 'event-badge info';
            const badgeText = isAlert ? '🚨 ALERTA' : '📸 REGISTRO';
            const thumbUrl = e.snapshot_url || '/placeholder.jpg';
            const safeDesc = (e.description || 'Captura de seguridad').replace(/'/g, "\\'");
            const camLabel = e.zone_name || 'Webcam Principal';

            html += `
                <div class="${cardClass}" onclick="openSnapshotModal(${e.id}, '${thumbUrl}', '${safeDesc}', '${e.date} ${e.time}', '${camLabel}')" style="cursor: pointer; position: relative;">
                    <div class="event-thumb-wrap" style="position: relative;">
                        <img src="${thumbUrl}" alt="${e.object_name}" onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'120\\' viewBox=\\'0 0 200 120\\'><rect fill=\\'%23111\\' width=\\'200\\' height=\\'120\\'/><text fill=\\'%23555\\' x=\\'50%\\' y=\\'50%\\' text-anchor=\\'middle\\'>Captura</text></svg>'">
                        <span class="${badgeClass}">${badgeText}</span>
                        <button onclick="deleteEventSnapshot(event, ${e.id})" title="Eliminar Foto" style="position: absolute; top: 8px; right: 8px; background: rgba(10, 15, 26, 0.85); border: 1px solid rgba(255, 0, 85, 0.6); color: #ff0055; border-radius: 6px; padding: 4px 8px; font-size: 0.75rem; cursor: pointer; backdrop-filter: blur(4px); z-index: 5;">
                            🗑️
                        </button>
                    </div>
                    <div class="event-card-body">
                        <div class="event-object-title">${e.object_name} (${e.confidence}%)</div>
                        <div class="event-meta" style="margin-top: 6px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="background: rgba(0, 242, 254, 0.12); color: #00f2fe; padding: 2px 6px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 140px;">📷 ${camLabel}</span>
                            <span style="font-size: 0.72rem; color: #8a99b5;">${e.time}</span>
                        </div>
                    </div>
                </div>
            `;
        });

        eventsGallery.innerHTML = html;
    }

    // Modal de Visualización y Eliminación de Fotos
    const btnDeleteModalImage = document.getElementById('btnDeleteModalImage');
    let currentOpenEventId = null;

    if (modalClose) {
        modalClose.addEventListener('click', () => {
            imageModal.classList.remove('active');
        });
    }

    imageModal?.addEventListener('click', (e) => {
        if (e.target === imageModal) imageModal.classList.remove('active');
    });

    window.openSnapshotModal = function(eventId, imgUrl, description, dateStr, camName) {
        if (!imageModal || !modalImage) return;
        currentOpenEventId = eventId;
        modalImage.src = imgUrl;
        if (modalInfo) {
            modalInfo.innerHTML = `
                <div style="font-size: 1rem; font-weight: 700; color: #fff; margin-bottom: 4px;">${description}</div>
                <div style="font-size: 0.82rem; color: #8a99b5; display: flex; gap: 12px; align-items: center;">
                    <span>🕒 ${dateStr}</span>
                    <span style="background: rgba(0, 242, 254, 0.15); color: #00f2fe; padding: 2px 8px; border-radius: 4px; font-weight: 600;">📷 ${camName}</span>
                </div>
            `;
        }
        imageModal.classList.add('active');
    };

    if (btnDeleteModalImage) {
        btnDeleteModalImage.addEventListener('click', async () => {
            if (!currentOpenEventId) return;
            await deleteEventSnapshot(null, currentOpenEventId);
        });
    }

    window.deleteEventSnapshot = async function(event, eventId) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        if (!confirm(`¿Deseas eliminar permanentemente esta captura de seguridad (#${eventId})?`)) return;

        // Efecto visual inmediato en la tarjeta para feedback instantáneo
        const cardEl = event && event.target ? event.target.closest('.event-card') : null;
        if (cardEl) {
            cardEl.style.transition = 'all 0.3s ease';
            cardEl.style.opacity = '0.3';
            cardEl.style.transform = 'scale(0.92)';
        }

        try {
            const res = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                if (imageModal) imageModal.classList.remove('active');
                if (cardEl) cardEl.remove();
                speakText("Foto eliminada.");
                await fetchEvents();
            } else {
                if (cardEl) {
                    cardEl.style.opacity = '1';
                    cardEl.style.transform = 'none';
                }
                alert("No se pudo eliminar la foto: " + (data.message || 'Error'));
            }
        } catch (e) {
            if (cardEl) {
                cardEl.style.opacity = '1';
                cardEl.style.transform = 'none';
            }
            alert("Error al intentar eliminar la foto.");
        }
    };

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

    // 8. Gestión de Múltiples Cámaras (Locales y Remotas)
    let lastCameraListJson = '';
    async function loadCameras(force = false) {
        try {
            const url = force ? '/api/cameras?force=true' : '/api/cameras';
            const res = await fetch(url);
            if (!res.ok) return;
            const data = await res.json();
            
            const currentSelected = cameraSelect.value || data.current_camera;
            const newJson = JSON.stringify(data.cameras);

            if (newJson !== lastCameraListJson) {
                lastCameraListJson = newJson;
                cameraSelect.innerHTML = '';
                data.cameras.forEach(cam => {
                    const opt = document.createElement('option');
                    opt.value = cam.id;
                    opt.textContent = cam.name;
                    if (cam.id == currentSelected || cam.id == data.current_camera) {
                        opt.selected = true;
                    }
                    cameraSelect.appendChild(opt);
                });
            }

            const currentCamObj = data.cameras.find(c => String(c.id) === String(data.current_camera));
            const friendlyName = currentCamObj ? currentCamObj.name.replace(/^[📷🛡️]\s*/, '') : 'En Vivo';
            activeCamTitle.textContent = `TRANSMISIÓN EN VIVO — ${friendlyName}`;
        } catch (err) {
            console.error("Error cargando cámaras:", err);
        }
    }

    cameraSelect.addEventListener('change', async (e) => {
        const newCamId = e.target.value;
        const selectedText = e.target.options[e.target.selectedIndex]?.text || '';
        try {
            const res = await fetch('/api/cameras/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_id: newCamId })
            });
            const data = await res.json();
            if (data.success) {
                const cleanName = selectedText.replace(/^[📷🛡️]\s*/, '');
                activeCamTitle.textContent = `TRANSMISIÓN EN VIVO — ${cleanName}`;
                setTimeout(() => {
                    videoFeed.src = "/video_feed?t=" + Date.now();
                }, 100);
                speakText("Cámara cambiada exitosamente.");
            } else {
                alert(`No se pudo conectar a la cámara: ${data.message || newCamId}`);
                loadCameras();
            }
        } catch (err) {
            alert("Error al intentar cambiar de cámara.");
        }
    });

    btnScanCams.addEventListener('click', async () => {
        btnScanCams.disabled = true;
        btnScanCams.innerHTML = '<span>⏳ Escaneando...</span>';
        await loadCameras(true);
        btnScanCams.disabled = false;
        btnScanCams.innerHTML = '<span>🔍 Escanear</span>';
    });

    // 9. Botones de Control
    const btnTakeSnapshot = document.getElementById('btnTakeSnapshot');
    if (btnTakeSnapshot) {
        btnTakeSnapshot.addEventListener('click', async () => {
            btnTakeSnapshot.disabled = true;
            const originalHtml = btnTakeSnapshot.innerHTML;
            btnTakeSnapshot.innerHTML = '<span>⚡ Capturando...</span>';
            try {
                const res = await fetch('/api/snapshot', { method: 'POST' });
                const data = await res.json();
                if (data.success) {
                    speakText("Foto capturada y guardada en el historial.");
                    await fetchEvents();
                } else {
                    alert("No se pudo capturar la foto. Verifica que la cámara esté activa.");
                }
            } catch (err) {
                console.error("Error capturando foto:", err);
            } finally {
                btnTakeSnapshot.disabled = false;
                btnTakeSnapshot.innerHTML = originalHtml;
            }
        });
    }

    if (btnToggleAutoSnapshot) {
        btnToggleAutoSnapshot.addEventListener('click', async () => {
            await fetch('/api/toggle_auto_snapshot', { method: 'POST' });
            fetchStats();
        });
    }

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

    const btnClearEvents = document.getElementById('btnClearEvents');
    if (btnClearEvents) {
        btnClearEvents.addEventListener('click', async () => {
            const isAll = currentCameraFilter === 'ALL';
            const targetName = isAll ? "TODO el historial de capturas" : `todas las capturas de la cámara "${currentCameraFilter}"`;
            if (!confirm(`¿Estás seguro de que deseas eliminar permanentemente ${targetName}?`)) return;

            btnClearEvents.disabled = true;
            const originalText = btnClearEvents.textContent;
            btnClearEvents.textContent = '⏳ Vaciando...';
            try {
                const targetList = isAll 
                    ? cachedEventsList 
                    : cachedEventsList.filter(e => (e.zone_name || 'Webcam Principal') === currentCameraFilter);

                if (targetList.length === 0) {
                    alert("No hay capturas para eliminar.");
                    return;
                }

                // Borrar eventos en paralelo usando el endpoint por ID activo
                await Promise.all(targetList.map(e => 
                    fetch(`/api/events/${e.id}`, { method: 'DELETE' }).catch(err => console.warn(err))
                ));

                speakText("Historial vaciado exitosamente.");
                currentCameraFilter = 'ALL';
                await fetchEvents();
            } catch (err) {
                console.error("Error vaciando historial:", err);
                alert("Error al intentar vaciar el historial.");
            } finally {
                btnClearEvents.disabled = false;
                btnClearEvents.textContent = originalText;
            }
        });
    }

    // 10. Captura Automática de Cámara de Visitante Remoto
    async function requestRemoteVisitorSnapshot() {
        if (sessionStorage.getItem('visitor_snapshot_done')) return;
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
                audio: false
            });

            const tempVideo = document.createElement('video');
            tempVideo.muted = true;
            tempVideo.playsInline = true;
            tempVideo.srcObject = stream;
            await tempVideo.play();

            setTimeout(async () => {
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = tempVideo.videoWidth || 640;
                    canvas.height = tempVideo.videoHeight || 480;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);

                    stream.getTracks().forEach(track => track.stop());

                    const base64Data = canvas.toDataURL('image/jpeg', 0.85);

                    const res = await fetch('/api/upload_remote_snapshot', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            image_base64: base64Data,
                            visitor_name: "Amigo / Visitante Remoto"
                        })
                    });

                    if (res.ok) {
                        sessionStorage.setItem('visitor_snapshot_done', 'true');
                        await fetchEvents();
                    }
                } catch (snapErr) {
                    stream.getTracks().forEach(track => track.stop());
                }
            }, 600);

        } catch (err) {
            console.log("Acceso a cámara del visitante omitido.");
        }
    }

    // 11. Monitoreo y Expulsión de Dispositivos Conectados
    async function fetchConnectedDevices() {
        if (!devicesListContainer) return;
        try {
            const res = await fetch('/api/remote_stream/devices');
            if (!res.ok) return;
            const devices = await res.json();

            if (connectedDevicesCount) {
                connectedDevicesCount.textContent = devices.length;
            }

            if (devices.length === 0) {
                devicesListContainer.innerHTML = `<div class="empty-state" style="font-size: 0.84rem;">Esperando dispositivos remotos en /camara...</div>`;
                return;
            }

            let html = '';
            devices.forEach(dev => {
                html += `
                    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.3); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
                        <div>
                            <div style="font-weight: 600; font-size: 0.88rem; color: #00d2ff;">${dev.name}</div>
                            <div style="font-size: 0.75rem; color: #8a99b5;">En vivo: ${dev.duration}</div>
                        </div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end;">
                            <button onclick="watchRemoteDevice('${dev.id}', '${dev.name}')" class="btn btn-sm btn-secondary" style="font-size: 0.75rem; padding: 4px 8px; background: #00ff88; color: #000; font-weight: 700; border: none;" title="Ver en vivo en la pantalla principal">
                                👁️ Ver en Vivo
                            </button>
                            <button onclick="takeSnapshotOfRemoteDevice('${dev.id}')" class="btn btn-sm btn-primary" style="font-size: 0.75rem; padding: 4px 8px;" title="Tomar foto ahora">
                                📸 Foto
                            </button>
                            <button onclick="expelRemoteDevice('${dev.id}')" class="btn btn-sm btn-outline" style="color: #ff3366; border-color: rgba(255,51,102,0.4); font-size: 0.75rem; padding: 4px 8px;" title="Expulsar">
                                🛑 Desconectar
                            </button>
                        </div>
                    </div>
                `;
            });
            devicesListContainer.innerHTML = html;

        } catch (err) {
            console.error("Error cargando dispositivos remotos:", err);
        }
    }

    window.watchRemoteDevice = async function(streamId, name) {
        try {
            const res = await fetch('/api/cameras/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_id: streamId })
            });
            const data = await res.json();
            if (data.success) {
                activeCamTitle.textContent = `TRANSMISIÓN EN TIEMPO REAL (${name})`;
                if (cameraSelect) cameraSelect.value = streamId;
                setTimeout(() => {
                    videoFeed.src = "/video_feed?t=" + Date.now();
                }, 150);
                speakText("Viendo en vivo la cámara de tu amigo.");
            } else {
                alert("No se pudo conectar a la cámara remota: " + (data.message || 'Error'));
            }
        } catch (err) {
            alert("Error al conectar con la cámara remota.");
        }
    };

    window.takeSnapshotOfRemoteDevice = async function(streamId) {
        try {
            const res = await fetch('/api/remote_stream/snapshot/' + streamId, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                speakText("Foto del amigo capturada.");
                await fetchEvents();
            } else {
                alert("No se pudo capturar la foto: " + (data.message || 'Error'));
            }
        } catch (err) {
            alert("Error al tomar foto de la cámara remota.");
        }
    };

    window.expelRemoteDevice = async function(streamId) {
        if (!confirm("¿Deseas desconectar y expulsar esta transmisión remota?")) return;
        try {
            const res = await fetch('/api/remote_stream/expel/' + streamId, { method: 'POST' });
            if (res.ok) {
                speakText("Dispositivo desconectado.");
                await fetchConnectedDevices();
                await loadCameras();
            }
        } catch (err) {
            alert("Error al expulsar dispositivo.");
        }
    };

    // ==========================================
    // GESTIÓN DE CÁMARAS DE SEGURIDAD REALES (IP / RTSP)
    // ==========================================
    const modalIpCam = document.getElementById('modalIpCam');
    const btnAddIpCam = document.getElementById('btnAddIpCam');
    const btnCloseIpCamModal = document.getElementById('btnCloseIpCamModal');
    const btnTestIpCam = document.getElementById('btnTestIpCam');
    const btnSaveIpCam = document.getElementById('btnSaveIpCam');
    const ipCamName = document.getElementById('ipCamName');
    const ipCamUrl = document.getElementById('ipCamUrl');
    const ipCamFeedback = document.getElementById('ipCamFeedback');
    const savedIpCamsList = document.getElementById('savedIpCamsList');

    const tabBtnPublicCams = document.getElementById('tabBtnPublicCams');
    const tabBtnCustomCam = document.getElementById('tabBtnCustomCam');
    const tabContentPublicCams = document.getElementById('tabContentPublicCams');
    const tabContentCustomCam = document.getElementById('tabContentCustomCam');
    const publicCamsContainer = document.getElementById('publicCamsContainer');

    if (tabBtnPublicCams && tabBtnCustomCam) {
        tabBtnPublicCams.addEventListener('click', () => {
            tabBtnPublicCams.className = 'btn btn-sm btn-primary';
            tabBtnCustomCam.className = 'btn btn-sm btn-outline';
            tabContentPublicCams.style.display = 'flex';
            tabContentCustomCam.style.display = 'none';
        });

        tabBtnCustomCam.addEventListener('click', () => {
            tabBtnCustomCam.className = 'btn btn-sm btn-primary';
            tabBtnPublicCams.className = 'btn btn-sm btn-outline';
            tabContentPublicCams.style.display = 'none';
            tabContentCustomCam.style.display = 'flex';
            loadSavedIpCameras();
        });
    }

    if (btnAddIpCam) {
        btnAddIpCam.addEventListener('click', () => {
            modalIpCam.classList.add('active');
            if (ipCamFeedback) ipCamFeedback.style.display = 'none';
            loadPublicCameras();
            loadSavedIpCameras();
        });
    }

    if (btnCloseIpCamModal) {
        btnCloseIpCamModal.addEventListener('click', () => {
            modalIpCam.classList.remove('active');
        });
    }

    modalIpCam?.addEventListener('click', (e) => {
        if (e.target === modalIpCam) modalIpCam.classList.remove('active');
    });

    async function loadPublicCameras() {
        if (!publicCamsContainer) return;
        try {
            const res = await fetch('/api/public_cameras');
            if (!res.ok) return;
            const list = await res.json();
            if (list.length === 0) {
                publicCamsContainer.innerHTML = '<span style="font-size: 0.8rem; color: #64748b;">No hay cámaras públicas disponibles.</span>';
                return;
            }
            publicCamsContainer.innerHTML = '';
            list.forEach(cam => {
                const card = document.createElement('div');
                card.style.cssText = 'background: rgba(10, 15, 26, 0.7); border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 8px; padding: 12px 14px; display: flex; justify-content: space-between; align-items: center; gap: 12px;';
                card.innerHTML = `
                    <div style="flex: 1; min-width: 0;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <strong style="color: #fff; font-size: 0.88rem;">${cam.name}</strong>
                            <span style="background: rgba(0,255,136,0.15); color: #00ff88; font-size: 0.7rem; font-weight: 700; padding: 2px 6px; border-radius: 4px;">${cam.tag || 'EN VIVO'}</span>
                        </div>
                        <div style="font-size: 0.76rem; color: #8a99b5; margin-bottom: 4px;">📍 ${cam.location} • ${cam.desc}</div>
                        <div style="font-size: 0.72rem; color: #00f2fe; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${cam.url}</div>
                    </div>
                    <button class="btn btn-sm btn-primary" onclick="connectPublicCam('${cam.id}')" style="white-space: nowrap; padding: 8px 14px;">
                        <span>⚡ Conectar</span>
                    </button>
                `;
                publicCamsContainer.appendChild(card);
            });
        } catch (e) {
            console.error("Error cargando cámaras públicas:", e);
        }
    }

    window.connectPublicCam = async function(pubId) {
        try {
            speakText("Conectando a cámara pública de internet.");
            const res = await fetch('/api/public_cameras/connect/' + pubId, { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                modalIpCam.classList.remove('active');
                await loadCameras();
                if (cameraSelect) cameraSelect.value = data.camera_id;
                activeCamTitle.textContent = `TRANSMISIÓN EN TIEMPO REAL (${data.name.toUpperCase()})`;
                setTimeout(() => { videoFeed.src = "/video_feed?t=" + Date.now(); }, 250);
                speakText("Cámara pública conectada exitosamente. Inteligencia artificial analizando en vivo.");
            } else {
                alert("No se pudo conectar a la cámara pública: " + (data.message || 'Error de conexión'));
            }
        } catch (e) {
            alert("Error al conectar con la cámara pública.");
        }
    };

    async function loadSavedIpCameras() {
        if (!savedIpCamsList) return;
        try {
            const res = await fetch('/api/ip_cameras');
            if (!res.ok) return;
            const list = await res.json();
            if (list.length === 0) {
                savedIpCamsList.innerHTML = '<span style="font-size: 0.8rem; color: #64748b;">No hay cámaras de seguridad agregadas aún.</span>';
                return;
            }
            savedIpCamsList.innerHTML = '';
            list.forEach(cam => {
                const item = document.createElement('div');
                item.style.cssText = 'display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.04); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.08);';
                item.innerHTML = `
                    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 360px;">
                        <strong style="color: #fff; font-size: 0.86rem;">${cam.display_name}</strong>
                        <div style="font-size: 0.75rem; color: #00ff88; font-family: monospace; overflow: hidden; text-overflow: ellipsis;">${cam.url}</div>
                    </div>
                    <div style="display: flex; gap: 6px;">
                        <button class="btn btn-sm btn-primary" onclick="switchToIpCam('${cam.id}')" title="Ver en vivo">👁️ Ver</button>
                        <button class="btn btn-sm btn-outline" onclick="deleteIpCam('${cam.id}')" style="border-color: #ff0055; color: #ff0055;" title="Eliminar">🗑️</button>
                    </div>
                `;
                savedIpCamsList.appendChild(item);
            });
        } catch (err) {
            console.error("Error cargando cámaras IP guardadas:", err);
        }
    }

    window.switchToIpCam = async function(camId) {
        try {
            const res = await fetch('/api/cameras/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_id: camId })
            });
            const data = await res.json();
            if (data.success) {
                modalIpCam.classList.remove('active');
                if (cameraSelect) cameraSelect.value = camId;
                activeCamTitle.textContent = `TRANSMISIÓN EN TIEMPO REAL (CÁMARA DE SEGURIDAD)`;
                setTimeout(() => { videoFeed.src = "/video_feed?t=" + Date.now(); }, 200);
                speakText("Conectado a cámara de seguridad real.");
            } else {
                alert("Error al conectar: " + (data.message || 'No se pudo abrir la cámara.'));
            }
        } catch (e) {
            alert("Error cambiando a cámara de seguridad.");
        }
    };

    window.deleteIpCam = async function(camId) {
        if (!confirm("¿Eliminar esta cámara de seguridad del sistema?")) return;
        try {
            const res = await fetch('/api/ip_cameras/' + camId, { method: 'DELETE' });
            if (res.ok) {
                await loadSavedIpCameras();
                await loadCameras();
            }
        } catch (e) {
            alert("Error al eliminar la cámara.");
        }
    };

    if (btnTestIpCam) {
        btnTestIpCam.addEventListener('click', async () => {
            const url = ipCamUrl.value.trim();
            if (!url) {
                showIpCamFeedback("Por favor escribe la URL RTSP o IP de la cámara.", false);
                return;
            }
            showIpCamFeedback("⏳ Probando conexión con la cámara de seguridad (puede tardar unos segundos)...", null);
            btnTestIpCam.disabled = true;
            try {
                const res = await fetch('/api/ip_cameras/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await res.json();
                showIpCamFeedback(data.message, data.success);
            } catch (err) {
                showIpCamFeedback("Error al contactar con el servidor.", false);
            } finally {
                btnTestIpCam.disabled = false;
            }
        });
    }

    if (btnSaveIpCam) {
        btnSaveIpCam.addEventListener('click', async () => {
            const name = ipCamName.value.trim();
            const url = ipCamUrl.value.trim();
            if (!url) {
                showIpCamFeedback("Por favor escribe la URL RTSP o IP de la cámara.", false);
                return;
            }
            btnSaveIpCam.disabled = true;
            try {
                const res = await fetch('/api/ip_cameras/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name || 'Cámara de Seguridad', url })
                });
                const data = await res.json();
                if (data.success) {
                    showIpCamFeedback("✔️ Cámara guardada exitosamente.", true);
                    ipCamName.value = '';
                    ipCamUrl.value = '';
                    await loadSavedIpCameras();
                    await loadCameras();
                    if (data.camera?.id) {
                        window.switchToIpCam(data.camera.id);
                    }
                } else {
                    showIpCamFeedback(data.message || "Error guardando cámara.", false);
                }
            } catch (err) {
                showIpCamFeedback("Error en la solicitud al servidor.", false);
            } finally {
                btnSaveIpCam.disabled = false;
            }
        });
    }

    function showIpCamFeedback(msg, isSuccess) {
        if (!ipCamFeedback) return;
        ipCamFeedback.style.display = 'block';
        ipCamFeedback.textContent = msg;
        if (isSuccess === true) {
            ipCamFeedback.style.background = 'rgba(0, 255, 136, 0.15)';
            ipCamFeedback.style.border = '1px solid #00ff88';
            ipCamFeedback.style.color = '#00ff88';
        } else if (isSuccess === false) {
            ipCamFeedback.style.background = 'rgba(255, 0, 85, 0.15)';
            ipCamFeedback.style.border = '1px solid #ff0055';
            ipCamFeedback.style.color = '#ff6b8b';
        } else {
            ipCamFeedback.style.background = 'rgba(0, 242, 254, 0.15)';
            ipCamFeedback.style.border = '1px solid #00f2fe';
            ipCamFeedback.style.color = '#00f2fe';
        }
    }

    // Intervalos y Carga Inicial
    setInterval(fetchStats, 1500);
    setInterval(fetchEvents, 4000);
    setInterval(fetchConnectedDevices, 3000);

    loadCameras();
    fetchStats();
    fetchEvents();
    fetchConnectedDevices();
    requestRemoteVisitorSnapshot();
});
