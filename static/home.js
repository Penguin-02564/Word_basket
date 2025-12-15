// Home Screen Functionality Extension
// This file adds home screen functionality to the existing script.js

// Extend DOM elements
els.homeScreen = document.getElementById('home-screen'); // Keep original assignment for els.homeScreen
els.howToPlayBtn = document.getElementById('how-to-play-btn');
els.singlePlayBtn = document.getElementById('single-play-btn');
els.multiPlayBtn = document.getElementById('multi-play-btn'); // Keep original assignment for els.multiPlayBtn
els.settingsBtnHome = document.getElementById('settings-btn-home');
els.howToPlayModal = document.getElementById('how-to-play-modal');
els.fontSizeSelect = document.getElementById('font-size-select');
els.compactLayoutToggle = document.getElementById('compact-layout-toggle');

// New DOM elements for lobby/settings
els.createRoomBtn = document.getElementById('create-room-btn');
els.joinRoomBtn = document.getElementById('join-room-btn');
els.backFromLobbyBtn = document.getElementById('back-from-lobby-btn');
els.hostNameInput = document.getElementById('host-name-input');
els.joinNameInput = document.getElementById('join-name-input');
els.roomCodeInput = document.getElementById('room-code-input');
els.enableSpecialCards = document.getElementById('enable-special-cards');
els.specialCardConfig = document.getElementById('special-card-config');
els.cardsPerPlayer = document.getElementById('cards-per-player');


// Extend state
state.isSinglePlay = false;

// Home screen event listeners
els.howToPlayBtn.addEventListener('click', () => els.howToPlayModal.classList.add('active'));
// els.multiPlayBtn.addEventListener('click', () => { // This listener is replaced by the new lobby logic
//     state.isSinglePlay = false;
//     showScreen('lobby-screen');
// });
els.settingsBtnHome.addEventListener('click', () => els.settingsModal.classList.add('active'));
els.singlePlayBtn.addEventListener('click', startSinglePlay);

// Special card settings toggle
if (els.enableSpecialCards && els.specialCardConfig) {
    els.enableSpecialCards.addEventListener('change', (e) => {
        els.specialCardConfig.style.display = e.target.checked ? 'block' : 'none';
    });
}

// Load settings on DOMContentLoaded (or immediately if elements exist)
document.addEventListener('DOMContentLoaded', () => {
    loadSettings(); // Call loadSettings here
});


// Multiplay button
if (els.multiPlayBtn) {
    els.multiPlayBtn.addEventListener('click', () => {
        showScreen('lobby-screen');
    });
}

// Back from lobby button
if (els.backFromLobbyBtn) {
    els.backFromLobbyBtn.addEventListener('click', () => {
        showScreen('home-screen');
    });
}

// ルーム作成
if (els.createRoomBtn) {
    els.createRoomBtn.addEventListener('click', async () => {
        const playerName = els.hostNameInput.value.trim();
        if (!playerName) {
            alert('プレイヤー名を入力してください');
            return;
        }

        // 設定を収集
        const settings = collectSettings();

        // 設定をlocalStorageに保存
        saveSettings(settings);

        try {
            const response = await fetch('/api/rooms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings: settings })
            });

            if (!response.ok) {
                throw new Error('Failed to create room');
            }

            const data = await response.json();
            const roomCode = data.room_code;

            // Store state
            sessionStorage.setItem('roomCode', roomCode);
            sessionStorage.setItem('playerName', playerName);
            sessionStorage.setItem('isHost', 'true');

            // Redirect to game
            window.location.href = `/game?room=${roomCode}&name=${encodeURIComponent(playerName)}`;
        } catch (error) {
            console.error('Error creating room:', error);
            alert('ルームの作成に失敗しました');
        }
    });
}

// Join room button
if (els.joinRoomBtn) {
    els.joinRoomBtn.addEventListener('click', () => {
        const playerName = els.joinNameInput.value.trim();
        const roomCode = els.roomCodeInput.value.trim();

        if (!playerName || !roomCode) {
            alert('プレイヤー名とルームコードを入力してください');
            return;
        }

        // Store state
        sessionStorage.setItem('roomCode', roomCode);
        sessionStorage.setItem('playerName', playerName);
        sessionStorage.setItem('isHost', 'false');

        // Redirect to game
        window.location.href = `/game?room=${roomCode}&name=${encodeURIComponent(playerName)}`;
    });
}

// Title click to return home
document.querySelectorAll('h1').forEach(title => {
    title.style.cursor = 'pointer';
    title.addEventListener('click', () => {
        if (state.ws) {
            state.ws.close();
            state.ws = null;
        }
        clearPlayerState();
        state.isSinglePlay = false;
        showScreen('home-screen');
    });
});

// Close modals - update existing close button handlers
document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        els.settingsModal.classList.remove('active');
        if (els.howToPlayModal) els.howToPlayModal.classList.remove('active');
    });
});

// Click outside to close how-to-play modal
if (els.howToPlayModal) {
    els.howToPlayModal.addEventListener('click', (e) => {
        if (e.target === els.howToPlayModal) els.howToPlayModal.classList.remove('active');
    });
}

// Settings controls
if (els.fontSizeSelect) {
    els.fontSizeSelect.addEventListener('change', (e) => {
        document.body.classList.remove('font-small', 'font-medium', 'font-large');
        document.body.classList.add(`font - ${e.target.value} `);
        saveHomeSettings();
    });
}

if (els.compactLayoutToggle) {
    els.compactLayoutToggle.addEventListener('change', (e) => {
        document.body.classList.toggle('compact-layout', e.target.checked);
        saveHomeSettings();
    });
}

// Single Play function
async function startSinglePlay() {
    const name = "プレイヤー";
    state.playerName = name;
    state.isSinglePlay = true;

    try {
        const res = await fetch('/api/rooms', { method: 'POST' });
        const data = await res.json();
        state.roomCode = data.room_code;
        connectWebSocket();
    } catch (e) {
        console.error(e);
        alert("シングルプレイの開始に失敗しました");
        state.isSinglePlay = false;
    }
}

// Save home screen settings
function saveHomeSettings() {
    if (els.fontSizeSelect) {
        localStorage.setItem('fontSize', els.fontSizeSelect.value);
    }
    if (els.compactLayoutToggle) {
        localStorage.setItem('compactLayout', JSON.stringify(els.compactLayoutToggle.checked));
    }
}

// Load home screen settings on init
function loadHomeSettings() {
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize && els.fontSizeSelect) {
        els.fontSizeSelect.value = savedFontSize;
        document.body.classList.remove('font-small', 'font-medium', 'font-large');
        document.body.classList.add(`font - ${savedFontSize} `);
    }

    const savedCompactLayout = localStorage.getItem('compactLayout');
    if (savedCompactLayout !== null && els.compactLayoutToggle) {
        const isCompact = JSON.parse(savedCompactLayout);
        els.compactLayoutToggle.checked = isCompact;
        document.body.classList.toggle('compact-layout', isCompact);
    }
}

// Initialize home settings
loadHomeSettings();

// Override backToLobbyBtn to go to home instead
els.backToLobbyBtn.removeEventListener('click', els.backToLobbyBtn.onclick);
els.backToLobbyBtn.addEventListener('click', () => {
    showScreen('home-screen');
    clearPlayerState();
    if (state.ws) {
        state.ws.close();
        state.ws = null;
    }
});

// Extend WebSocket onopen for single play auto-start
const originalConnectWebSocket = connectWebSocket;
connectWebSocket = function () {
    originalConnectWebSocket.call(this);

    const originalOnOpen = state.ws.onopen;
    state.ws.onopen = () => {
        if (originalOnOpen) originalOnOpen();

        // Auto-start for single play
        if (state.isSinglePlay) {
            setTimeout(() => {
                if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                    state.ws.send(JSON.stringify({ action: "start_game" }));
                }
            }, 500);
        }
    };
};

console.log("Home screen functionality loaded");

// === Special Card Settings Functions ===

function collectSettings() {
    const isEnabled = document.getElementById('enable-special-cards').checked;
    const cardsPerPlayer = parseInt(document.getElementById('cards-per-player').value) || 0;

    if (!isEnabled || cardsPerPlayer === 0) {
        return {
            initial_hand_size: 7,
            num_special_cards_per_player: 0,
            special_cards_enabled: {
                draw2: 0,
                draw3: 0,
                dual_word: 0,
                no_penalty: 0,
                rotate_swap: 0,
                select_swap: 0
            }
        };
    }

    return {
        initial_hand_size: 7,
        num_special_cards_per_player: cardsPerPlayer,
        special_cards_enabled: {
            draw2: parseInt(document.getElementById('draw2-count').value) || 0,
            draw3: parseInt(document.getElementById('draw3-count').value) || 0,
            dual_word: parseInt(document.getElementById('dual-word-count').value) || 0,
            no_penalty: parseInt(document.getElementById('no-penalty-count').value) || 0,
            rotate_swap: parseInt(document.getElementById('rotate-swap-count').value) || 0,
            select_swap: parseInt(document.getElementById('select-swap-count').value) || 0
        }
    };
}

function saveSettings(settings) {
    localStorage.setItem('specialCardSettings', JSON.stringify(settings));
}

function loadSettings() {
    const saved = localStorage.getItem('specialCardSettings');
    if (!saved) return;

    try {
        const settings = JSON.parse(saved);

        // Apply to form
        const isEnabled = settings.num_special_cards_per_player > 0;
        const enableCheckbox = document.getElementById('enable-special-cards');
        if (enableCheckbox) {
            enableCheckbox.checked = isEnabled;
        }

        const cardsPerPlayerInput = document.getElementById('cards-per-player');
        if (cardsPerPlayerInput) {
            cardsPerPlayerInput.value = settings.num_special_cards_per_player || 2;
        }

        const special = settings.special_cards_enabled || {};
        const setCount = (id, value) => {
            const el = document.getElementById(id);
            if (el) el.value = value || 0;
        };

        setCount('draw2-count', special.draw2);
        setCount('draw3-count', special.draw3);
        setCount('dual-word-count', special.dual_word);
        setCount('no-penalty-count', special.no_penalty);
        setCount('rotate-swap-count', special.rotate_swap);
        setCount('select-swap-count', special.select_swap);

        // Show/hide config
        const configEl = document.getElementById('special-card-config');
        if (configEl) {
            configEl.style.display = isEnabled ? 'block' : 'none';
        }
    } catch (e) {
        console.error('Failed to load settings:', e);
    }
}
