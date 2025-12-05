// DOM Elements
const els = {
    // Screens
    lobbyScreen: document.getElementById('lobby-screen'),
    waitingScreen: document.getElementById('waiting-screen'),
    gameScreen: document.getElementById('game-screen'),

    // Lobby
    playerNameInput: document.getElementById('player-name-input'),
    createRoomBtn: document.getElementById('create-room-btn'),
    roomCodeInput: document.getElementById('room-code-input'),
    joinRoomBtn: document.getElementById('join-room-btn'),

    // Waiting
    displayRoomCode: document.getElementById('display-room-code'),
    copyCodeBtn: document.getElementById('copy-code-btn'),
    playersList: document.getElementById('players-list'),
    startGameBtn: document.getElementById('start-game-btn'),
    waitingMessage: document.getElementById('waiting-message'),

    // Game
    currentWord: document.getElementById('current-word'),
    targetChar: document.getElementById('target-char'),
    deckCount: document.getElementById('deck-count'),
    handCount: document.getElementById('hand-count'),
    wordInput: document.getElementById('word-input'),
    submitBtn: document.getElementById('submit-btn'),
    messageArea: document.getElementById('message-area'),
    hand: document.getElementById('hand'),
    handLabel: document.getElementById('hand-label'),
    rerollBtn: document.getElementById('reroll-btn'),
    menuBtn: document.getElementById('menu-btn'),
    opponentsArea: document.getElementById('opponents-area'),

    // Modal
    settingsModal: document.getElementById('settings-modal'),
    closeModalBtn: document.querySelector('.close-btn'),
    priorityList: document.getElementById('priority-list'),
    autoSelectToggle: document.getElementById('auto-select-toggle'),

    // Result
    resultScreen: document.getElementById('result-screen'),
    resultList: document.getElementById('result-list'),
    backToLobbyBtn: document.getElementById('back-to-lobby-btn')
};

// State
let state = {
    roomCode: null,
    playerName: "",
    playerId: null,
    isHost: false,
    ws: null,
    hand: [],
    selectedCardIndex: -1,
    autoSelect: false,
    cardPriority: ['char', 'row', 'length'],
    reconnectTimer: null
};

// --- Initialization ---

function init() {
    setupEventListeners();
    loadSettings();
    loadPlayerState();
}

function setupEventListeners() {
    // Lobby
    els.createRoomBtn.addEventListener('click', createRoom);
    els.joinRoomBtn.addEventListener('click', joinRoom);

    // Waiting
    els.copyCodeBtn.addEventListener('click', copyRoomCode);
    els.startGameBtn.addEventListener('click', sendStartGame);

    // Game
    els.submitBtn.addEventListener('click', submitWord);
    els.wordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') submitWord();
    });
    els.wordInput.addEventListener('input', handleInput);
    els.rerollBtn.addEventListener('click', sendReroll);

    // Result
    els.backToLobbyBtn.addEventListener('click', () => {
        showScreen('lobby-screen');
        clearPlayerState();
        // Close connection
        if (state.ws) {
            state.ws.close();
            state.ws = null;
        }
    });

    // Settings
    els.menuBtn.addEventListener('click', () => els.settingsModal.classList.add('active'));
    els.closeModalBtn.addEventListener('click', () => els.settingsModal.classList.remove('active'));
    els.settingsModal.addEventListener('click', (e) => {
        if (e.target === els.settingsModal) els.settingsModal.classList.remove('active');
    });
    els.autoSelectToggle.addEventListener('change', (e) => {
        state.autoSelect = e.target.checked;
        saveSettings();
        if (state.autoSelect) {
            handleInput(); // Trigger auto-select immediately
        } else {
            clearAutoSelection();
        }
    });

    setupDragAndDrop();
}

// --- WebSocket & Connection ---

async function createRoom() {
    const name = els.playerNameInput.value.trim();
    if (!name) {
        alert("名前を入力してください");
        return;
    }
    state.playerName = name;

    try {
        const res = await fetch('/api/rooms', { method: 'POST' });
        const data = await res.json();
        state.roomCode = data.room_code;
        connectWebSocket();
    } catch (e) {
        console.error(e);
        alert("ルーム作成に失敗しました");
    }
}

function joinRoom() {
    const name = els.playerNameInput.value.trim();
    const code = els.roomCodeInput.value.trim();

    if (!name) {
        alert("名前を入力してください");
        return;
    }
    if (!code || code.length !== 4) {
        alert("正しいルームコードを入力してください");
        return;
    }

    state.playerName = name;
    state.roomCode = code;
    connectWebSocket();
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${protocol}//${window.location.host}/ws/${state.roomCode}/${encodeURIComponent(state.playerName)}`;

    // Add player_id if we have it (for reconnection)
    if (state.playerId) {
        wsUrl += `?player_id=${state.playerId}`;
    }

    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        console.log("Connected to WebSocket");
        showScreen('waiting-screen');
        els.displayRoomCode.textContent = state.roomCode;
        // Clear any existing reconnect timer
        if (state.reconnectTimer) {
            clearTimeout(state.reconnectTimer);
            state.reconnectTimer = null;
        }
    };

    state.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };

    state.ws.onclose = (event) => {
        console.log("Disconnected", event);
        if (event.code === 4000) {
            alert("ルームが見つかりません");
            showScreen('lobby-screen');
            clearPlayerState();
        } else {
            // Attempt auto-reconnect
            console.log("Attempting to reconnect...");
            if (!state.reconnectTimer) {
                state.reconnectTimer = setTimeout(() => {
                    state.reconnectTimer = null;
                    if (state.roomCode && state.playerName) {
                        connectWebSocket();
                    }
                }, 3000);
            }
        }
    };

    state.ws.onerror = (error) => {
        console.error("WebSocket Error", error);
    };
}

function handleMessage(data) {
    if (data.type === 'game_state') {
        updateGameState(data);
    } else if (data.type === 'error') {
        showMessage(data.message, true);
    } else if (data.type === 'return_to_title') {
        alert(data.message);
        showScreen('lobby-screen');
        clearPlayerState();
        if (state.ws) {
            state.ws.close();
            state.ws = null;
        }
    }
}

function sendStartGame() {
    state.ws.send(JSON.stringify({ action: "start_game" }));
}

function sendPlayWord(word, cardIndex) {
    state.ws.send(JSON.stringify({
        action: "play_word",
        word: word,
        card_index: cardIndex
    }));
}

function sendReroll() {
    if (confirm("手札をリロールしますか？（手札が1枚増えます）")) {
        state.ws.send(JSON.stringify({ action: "reroll" }));
    }
}

function sendPriority() {
    state.ws.send(JSON.stringify({
        action: "set_priority",
        priority: state.cardPriority
    }));
}

// --- UI Updates ---

function showScreen(screenId) {
    Object.values(els).forEach(el => {
        if (el instanceof HTMLElement && el.classList.contains('screen')) {
            el.classList.remove('active');
        }
    });
    document.getElementById(screenId).classList.add('active');
}

function updateGameState(data) {
    // Update basic info
    state.playerId = data.my_player_id;
    state.isHost = data.is_host;
    state.hand = data.my_hand || [];

    // Save player ID for reconnection
    if (state.playerId) {
        savePlayerState();
    }

    // Update Waiting Screen
    if (data.status === 'waiting') {
        showScreen('waiting-screen');
        renderPlayersList(data.players_info);

        if (state.isHost) {
            els.startGameBtn.classList.remove('hidden');
            els.waitingMessage.classList.add('hidden');
        } else {
            els.startGameBtn.classList.add('hidden');
            els.waitingMessage.classList.remove('hidden');
        }
    }
    // Update Game Screen
    else if (data.status === 'playing' || data.status === 'finished') {
        if (!document.getElementById('game-screen').classList.contains('active')) {
            showScreen('game-screen');
        }

        els.currentWord.textContent = data.current_word;
        els.targetChar.textContent = data.target_char;
        els.deckCount.textContent = data.deck_count;
        els.handCount.textContent = state.hand.length;

        renderHand();
        renderOpponents(data.players_info);

        if (data.message) {
            showMessage(data.message, false);
        }

        if (data.message) {
            showMessage(data.message, false);
        }

        // Handle finished state for self
        const myPlayer = data.players_info.find(p => p.player_id === state.playerId);
        if (myPlayer && myPlayer.rank) {
            els.wordInput.disabled = true;
            els.submitBtn.disabled = true;
            els.wordInput.placeholder = `${myPlayer.rank}位で上がりました！他のプレイヤーを待っています...`;
        } else {
            els.wordInput.disabled = false;
            els.submitBtn.disabled = false;
            els.wordInput.placeholder = "単語を入力 (ひらがな)";
        }

        if (data.game_over) {
            renderResultScreen(data.ranks);
            showScreen('result-screen');

            // Hide back button for non-hosts
            if (state.isHost) {
                els.backToLobbyBtn.classList.remove('hidden');
            } else {
                els.backToLobbyBtn.classList.add('hidden');
            }
        }
    }
}

function renderResultScreen(ranks) {
    els.resultList.innerHTML = '';
    ranks.forEach(p => {
        const li = document.createElement('li');
        li.className = 'result-item';
        li.innerHTML = `
            <span class="rank">${p.rank}位</span>
            <span class="name">${p.name}</span>
        `;
        els.resultList.appendChild(li);
    });
}

function renderPlayersList(players) {
    els.playersList.innerHTML = '';
    players.forEach(p => {
        const li = document.createElement('li');
        li.className = `player-item ${p.player_id === state.playerId ? 'is-me' : ''}`;
        li.innerHTML = `
            <span class="player-name">${p.name} ${p.is_host ? '👑' : ''} ${p.rank ? `(${p.rank}位)` : ''}</span>
            <span class="player-status">${p.player_id === state.playerId ? '(あなた)' : ''}</span>
        `;
        els.playersList.appendChild(li);
    });
}

function renderOpponents(players) {
    els.opponentsArea.innerHTML = '';
    players.forEach(p => {
        if (p.player_id !== state.playerId) {
            const div = document.createElement('div');
            div.className = 'opponent-card';
            div.innerHTML = `
                <div class="name">${p.name} ${p.rank ? `(${p.rank}位)` : ''}</div>
                <div class="count">${p.rank ? '🎉' : '🎴 ' + p.hand_count}</div>
            `;
            els.opponentsArea.appendChild(div);
        }
    });
}

function renderHand() {
    els.hand.innerHTML = '';

    // Two rows logic
    if (state.hand.length >= 8) {
        els.hand.classList.add('two-rows');
    } else {
        els.hand.classList.remove('two-rows');
    }

    state.hand.forEach((card, index) => {
        const cardEl = document.createElement('div');
        cardEl.className = 'card';
        if (index === state.selectedCardIndex) {
            cardEl.classList.add('selected');
        }

        cardEl.innerHTML = `
            <div class="card-value">${card.display}</div>
            <div class="card-type">${getCardTypeLabel(card.type)}</div>
        `;

        cardEl.addEventListener('click', () => selectCard(index));
        els.hand.appendChild(cardEl);
    });

    // Re-apply auto-select highlight if input has text
    if (state.autoSelect && els.wordInput.value) {
        highlightAutoSelectedCard(els.wordInput.value);
    }
}

function getCardTypeLabel(type) {
    if (type === 'char') return '文字';
    if (type === 'row') return '行';
    if (type === 'length') return '文字数';
    return '';
}

function selectCard(index) {
    if (state.selectedCardIndex === index) {
        state.selectedCardIndex = -1; // Deselect
    } else {
        state.selectedCardIndex = index;
    }
    renderHand();
}

function handleInput() {
    const word = els.wordInput.value;
    if (state.autoSelect) {
        highlightAutoSelectedCard(word);
    }
}

function highlightAutoSelectedCard(word) {
    const bestIndex = findBestCardIndex(word);

    // Update UI
    const cards = document.querySelectorAll('.card');
    cards.forEach(c => c.classList.remove('auto-selected'));

    if (bestIndex !== -1 && cards[bestIndex]) {
        cards[bestIndex].classList.add('auto-selected');
    }
}

function findBestCardIndex(word) {
    if (!word) return -1;

    // Helper to normalize
    const normalize = (char) => {
        const map = {
            'が': 'か', 'ぎ': 'き', 'ぐ': 'く', 'げ': 'け', 'ご': 'こ',
            'ざ': 'さ', 'じ': 'し', 'ず': 'す', 'ぜ': 'せ', 'ぞ': 'そ',
            'だ': 'た', 'ぢ': 'ち', 'づ': 'つ', 'で': 'て', 'ど': 'と',
            'ば': 'は', 'び': 'ひ', 'ぶ': 'ふ', 'べ': 'へ', 'ぼ': 'ほ',
            'ぱ': 'は', 'ぴ': 'ひ', 'ぷ': 'ふ', 'ぺ': 'へ', 'ぽ': 'ほ',
            'ゃ': 'や', 'ゅ': 'ゆ', 'ょ': 'よ'
        };
        return map[char] || char;
    };

    let effectiveEnd = word.slice(-1);
    if (word.endsWith('ー') && word.length > 1) {
        effectiveEnd = word.slice(-2, -1);
    }
    const normEnd = normalize(effectiveEnd);

    const indicesByType = { char: [], row: [], length: [] };

    state.hand.forEach((card, idx) => {
        if (card.type === 'char') {
            if (normalize(card.value) === normEnd) indicesByType.char.push(idx);
        } else if (card.type === 'row') {
            if (card.value.split('').some(c => normalize(c) === normEnd)) indicesByType.row.push(idx);
        } else if (card.type === 'length') {
            const reqLen = parseInt(card.value);
            if (reqLen === 7) {
                if (word.length >= 7) indicesByType.length.push(idx);
            } else {
                if (word.length === reqLen) indicesByType.length.push(idx);
            }
        }
    });

    for (const type of state.cardPriority) {
        if (indicesByType[type].length > 0) return indicesByType[type][0];
    }

    return -1;
}

function submitWord() {
    const word = els.wordInput.value.trim();
    if (!word) return;

    let cardIndex = state.selectedCardIndex;

    if (state.autoSelect) {
        cardIndex = -1;
    } else {
        if (cardIndex === -1) {
            showMessage("カードを選択してください", true);
            return;
        }
    }

    sendPlayWord(word, cardIndex);
    els.wordInput.value = '';
    state.selectedCardIndex = -1;
    renderHand();
}

function showMessage(msg, isError) {
    els.messageArea.textContent = msg;
    els.messageArea.className = `message ${isError ? 'error' : 'success'}`;
    setTimeout(() => {
        els.messageArea.textContent = '';
        els.messageArea.className = 'message';
    }, 3000);
}

function copyRoomCode() {
    navigator.clipboard.writeText(state.roomCode).then(() => {
        alert("ルームコードをコピーしました");
    });
}

// --- Settings & Persistence ---

function loadSettings() {
    const savedPriority = localStorage.getItem('cardPriority');
    if (savedPriority) {
        state.cardPriority = JSON.parse(savedPriority);
    }

    const savedAutoSelect = localStorage.getItem('autoSelect');
    if (savedAutoSelect !== null) {
        state.autoSelect = JSON.parse(savedAutoSelect);
        els.autoSelectToggle.checked = state.autoSelect;
    }

    renderPriorityList();
}

function saveSettings() {
    localStorage.setItem('cardPriority', JSON.stringify(state.cardPriority));
    localStorage.setItem('autoSelect', JSON.stringify(state.autoSelect));

    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        sendPriority();
    }
}

function loadPlayerState() {
    const savedId = localStorage.getItem('playerId');
    const savedRoom = localStorage.getItem('roomCode');
    const savedName = localStorage.getItem('playerName');

    if (savedId && savedRoom && savedName) {
        state.playerId = savedId;
        state.roomCode = savedRoom;
        state.playerName = savedName;

        // Auto-join if we have saved state
        // But maybe user wants to start fresh?
        // Let's just pre-fill the inputs or auto-connect?
        // For "reconnection", auto-connect is better.
        // But if the game is over, we shouldn't.
        // Let's try to connect. If room doesn't exist, it will fail and clear state.
        console.log("Found saved session, attempting reconnect...");
        connectWebSocket();
    }
}

function savePlayerState() {
    localStorage.setItem('playerId', state.playerId);
    localStorage.setItem('roomCode', state.roomCode);
    localStorage.setItem('playerName', state.playerName);
}

function clearPlayerState() {
    localStorage.removeItem('playerId');
    localStorage.removeItem('roomCode');
    localStorage.removeItem('playerName');
    state.playerId = null;
    state.roomCode = null;
}

function renderPriorityList() {
    const items = Array.from(els.priorityList.children);
    items.sort((a, b) => {
        return state.cardPriority.indexOf(a.dataset.type) - state.cardPriority.indexOf(b.dataset.type);
    });
    items.forEach(item => els.priorityList.appendChild(item));
}

function setupDragAndDrop() {
    let draggedItem = null;
    const items = els.priorityList.querySelectorAll('.priority-item');

    items.forEach(item => {
        item.draggable = true;

        item.addEventListener('dragstart', (e) => {
            draggedItem = item;
            setTimeout(() => item.classList.add('dragging'), 0);
        });

        item.addEventListener('dragend', () => {
            draggedItem = null;
            item.classList.remove('dragging');
            updatePriorityFromDOM();
        });
    });

    els.priorityList.addEventListener('dragover', (e) => {
        e.preventDefault();
        const afterElement = getDragAfterElement(els.priorityList, e.clientY);
        if (afterElement == null) {
            els.priorityList.appendChild(draggedItem);
        } else {
            els.priorityList.insertBefore(draggedItem, afterElement);
        }
    });
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.priority-item:not(.dragging)')];

    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

function updatePriorityFromDOM() {
    const newPriority = [];
    els.priorityList.querySelectorAll('.priority-item').forEach((item, index) => {
        newPriority.push(item.dataset.type);
        item.querySelector('.priority-number').textContent = index + 1;
    });
    state.cardPriority = newPriority;
    saveSettings();
}

function clearAutoSelection() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(c => c.classList.remove('auto-selected'));
}

// Start
init();
