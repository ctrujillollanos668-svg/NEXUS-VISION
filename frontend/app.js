/**
 * NEXUS VISION — Controlador Frontend del Dashboard
 */

document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const liveClock = document.getElementById('liveClock');
    const systemStatusText = document.getElementById('systemStatusText');
    const globalAlertBanner = document.getElementById('globalAlertBanner');
    const globalAlertText = document.getElementById('globalAlertText');

    const fpsVal = document.getElementById('fpsVal');
    const motionVal = document.getElementById('motionVal');
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
    const btnToggleSound = document.getElementById('btnToggleSound');
    const soundBtnText = document.getElementById('soundBtnText');
    const btnRefresh = document.getElementById('btnRefresh');
    const btnReloadEvents = document.getElementById('btnReloadEvents');

    const eventsGallery = document.getElementById('eventsGallery');
    const videoFeed = document.getElementById('videoFeed');

    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalInfo = document.getElementById('modalInfo');
    const modalClose = document.getElementById('modalClose');

    // Elementos de Chat con IA
    const chatMessages = document.getElementById('chatMessages');
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chipButtons = document.querySelectorAll('.chip-btn');

    // 1. Reloj en Vivo
    function updateClock() {
        const now = new Date();
        liveClock.textContent = now.toLocaleTimeString('es-CO', { hour12: false });
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. Obtener Métricas en Vivo (/api/stats)
    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (!res.ok) return;
            const data = await res.json();

            systemStatusText.textContent = data.status;
            fpsVal.textContent = data.fps.toFixed(1);
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

            if (data.sound_enabled) {
                soundBtnText.textContent = "Alarma Sonora (ON)";
                btnToggleSound.className = "btn btn-secondary";
            } else {
                soundBtnText.textContent = "Alarma Sonora (SILENCIADA)";
                btnToggleSound.className = "btn btn-outline";
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

    // 3. Obtener Historial de Eventos de la Base de Datos (/api/events)
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

    // 4. Chat con Asistente de IA (/api/chat)
    async function sendChatMessage(msg) {
        if (!msg || msg.trim() === '') return;

        // Agregar burbuja del usuario
        appendChatBubble('user', 'Tú', msg);
        chatInput.value = '';

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });

            if (res.ok) {
                const data = await res.json();
                // Renderizar respuesta con markdown simple (negritas y saltos de línea)
                let formatted = data.reply
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/\n/g, '<br>');
                appendChatBubble('ai', '🤖 Nexus AI', formatted, true);
            } else {
                appendChatBubble('ai', '🤖 Nexus AI', 'Lo siento, ocurrió un error procesando tu consulta.');
            }
        } catch (err) {
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

        // Auto-scroll al final del chat
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

    // 5. Modal de Capturas
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

    // 6. Botones de Control
    btnToggleMotion.addEventListener('click', async () => {
        await fetch('/api/toggle_motion', { method: 'POST' });
        fetchStats();
    });

    btnToggleZones.addEventListener('click', async () => {
        await fetch('/api/toggle_zones', { method: 'POST' });
        fetchStats();
    });

    btnToggleSound.addEventListener('click', async () => {
        await fetch('/api/toggle_sound', { method: 'POST' });
        fetchStats();
    });

    btnRefresh.addEventListener('click', () => {
        videoFeed.src = "/video_feed?t=" + new Date().getTime();
    });

    btnReloadEvents.addEventListener('click', () => {
        fetchEvents();
    });

    // Intervalos
    setInterval(fetchStats, 1500);
    setInterval(fetchEvents, 4000);

    fetchStats();
    fetchEvents();
});
