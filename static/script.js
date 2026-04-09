// Chat functionality
let chatMessages = document.getElementById('chatMessages');
let messageInput = document.getElementById('messageInput');
let sendButton = document.getElementById('sendButton');
let loadingOverlay = document.getElementById('loadingOverlay');
let sessionList = document.getElementById('sessionList');
let newSessionButton = document.getElementById('newSessionButton');

let currentSessionId = null;
let currentSessionName = '';

function renderWelcomeMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = '🤖';

    const content = document.createElement('div');
    content.className = 'message-content';

    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = 'FPL Assistant';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.innerHTML = `Welcome to FPL Assistant! I'm your AI-powered Fantasy Premier League manager.<br><br>
        I can help you:<ul>
            <li>Compare players by stats and form</li>
            <li>Check injury status and news</li>
            <li>Analyze recent performance</li>
            <li>Get AI-powered transfer suggestions</li>
            <li>Answer general FPL questions</li>
        </ul>
        <br>Type <code>help</code> to see all commands or click the commands on the left to try them out!`;

    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString();

    content.appendChild(header);
    content.appendChild(messageText);
    content.appendChild(time);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);
}

function clearChatMessages() {
    if (chatMessages) {
        chatMessages.innerHTML = '';
    }
}

async function initializeSessions() {
    if (!newSessionButton || !sessionList) return;
    newSessionButton.addEventListener('click', () => createNewSession('New Chat'));
    await fetchSessions();
}

async function fetchSessions() {
    try {
        const response = await fetch('/sessions');
        const data = await response.json();
        const sessions = data.sessions || [];

        if (!sessions.length) {
            await createNewSession('New Chat');
            return;
        }

        renderSessionList(sessions);
        const activeSessionId = data.active_session_id || (sessions[0] && sessions[0].id);
        const activeSession = sessions.find(session => Number(session.id) === Number(activeSessionId)) || sessions[0];
        if (activeSession) {
            await loadSession(activeSession.id, activeSession.name);
        }
    } catch (error) {
        console.error('Error fetching sessions:', error);
        if (sessionList) {
            sessionList.innerHTML = '<div class="session-empty">Unable to load sessions.</div>';
        }
    }
}

function renderSessionList(sessions) {
    if (!sessionList) return;
    sessionList.innerHTML = '';

    sessions.forEach(session => {
        const item = document.createElement('button');
        item.className = 'session-item';
        item.dataset.sessionId = session.id;
        item.type = 'button';
        item.innerHTML = `<span class="session-name">${session.name || 'New Chat'}</span><span class="session-time">${new Date(session.created_at).toLocaleString()}</span>`;
        item.addEventListener('click', () => loadSession(session.id, session.name));
        if (Number(session.id) === Number(currentSessionId)) {
            item.classList.add('active');
        }
        sessionList.appendChild(item);
    });
}

async function createNewSession(name) {
    try {
        const response = await fetch('/sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name }),
        });
        const data = await response.json();
        if (!data.session_id) {
            throw new Error('Session creation failed');
        }
        await fetchSessions();
    } catch (error) {
        console.error('Error creating session:', error);
        alert('Unable to create a new chat session. Please try again.');
    }
}

async function loadSession(sessionId, sessionName) {
    if (!sessionId) return;
    currentSessionId = sessionId;
    currentSessionName = sessionName || 'Chat';
    updateActiveSessionUI();

    try {
        const response = await fetch(`/sessions/${sessionId}/history`);
        if (!response.ok) {
            throw new Error('Session history not found');
        }
        const data = await response.json();
        clearChatMessages();
        if (!data.history || !data.history.length) {
            renderWelcomeMessage();
        } else {
            data.history.forEach(message => addMessage(message.message, message.role));
        }
    } catch (error) {
        console.error('Error loading session history:', error);
        clearChatMessages();
        renderWelcomeMessage();
    }
}

function updateActiveSessionUI() {
    if (!sessionList) return;
    const items = sessionList.querySelectorAll('.session-item');
    items.forEach(item => {
        item.classList.toggle('active', Number(item.dataset.sessionId) === Number(currentSessionId));
    });
}

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    if (!currentSessionId) {
        await createNewSession('New Chat');
    }

    addMessage(message, 'user');
    messageInput.value = '';
    sendButton.disabled = true;
    showLoading(true);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message, session_id: currentSessionId }),
        });

        const data = await response.json();
        addMessage(data.response, 'bot');
    } catch (error) {
        console.error('Error:', error);
        addMessage('Sorry, I encountered an error. Please try again.', 'bot');
    } finally {
        sendButton.disabled = false;
        showLoading(false);
        scrollToBottom();
    }
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = type === 'bot' ? '🤖' : '👤';

    const content = document.createElement('div');
    content.className = 'message-content';

    const header = document.createElement('div');
    header.className = 'message-header';
    header.textContent = type === 'bot' ? 'FPL Assistant' : 'You';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.innerHTML = formatMessage(text);

    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = new Date().toLocaleTimeString();

    content.appendChild(header);
    content.appendChild(messageText);
    content.appendChild(time);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function formatMessage(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function insertCommand(command) {
    messageInput.value = command;
    messageInput.focus();
    messageInput.select();
}

function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

function scrollToBottom() {
    setTimeout(() => {
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }, 100);
}

document.addEventListener('DOMContentLoaded', () => {
    if (messageInput) {
        messageInput.focus();
    }
    if (sessionList) {
        initializeSessions();
    }
    setTimeout(() => {
        scrollToBottom();
    }, 500);
});

window.addEventListener('resize', () => {
    scrollToBottom();
});

document.addEventListener('click', (e) => {
    if (e.target.tagName === 'CODE') {
        const text = e.target.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const original = e.target.textContent;
            e.target.textContent = '✓ Copied!';
            e.target.style.background = 'rgba(0, 255, 136, 0.2)';
            setTimeout(() => {
                e.target.textContent = original;
                e.target.style.background = '';
            }, 1000);
        });
    }
});
