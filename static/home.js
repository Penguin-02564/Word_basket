// Home Screen Functionality Extension
// This file adds home screen functionality to the existing script.js

// Extend DOM elements
els.homeScreen = document.getElementById('home-screen');
els.howToPlayBtn = document.getElementById('how-to-play-btn');
els.singlePlayBtn = document.getElementById('single-play-btn');
els.multiPlayBtn = document.getElementById('multi-play-btn');
els.settingsBtnHome = document.getElementById('settings-btn-home');
els.howToPlayModal = document.getElementById('how-to-play-modal');
els.fontSizeSelect = document.getElementById('font-size-select');
els.compactLayoutToggle = document.getElementById('compact-layout-toggle');

// Extend state
state.isSinglePlay = false;

// Home screen event listeners
els.howToPlayBtn.addEventListener('click', () => els.howToPlayModal.classList.add('active'));
els.multiPlayBtn.addEventListener('click', () => showScreen('lobby-screen'));
els.settingsBtnHome.addEventListener('click', () => els.settingsModal.classList.add('active'));
els.singlePlayBtn.addEventListener('click', startSinglePlay);

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
        document.body.classList.add(`font-${e.target.value}`);
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
        document.body.classList.add(`font-${savedFontSize}`);
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
