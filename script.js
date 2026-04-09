// Chat functionality
let chatMessages = document.getElementById('chatMessages');
let messageInput = document.getElementById('messageInput');
let sendButton = document.getElementById('sendButton');
let loadingOverlay = document.getElementById('loadingOverlay');

// Initialize welcome message timestamp
document.getElementById('welcomeTime').textContent = new Date().toLocaleTimeString();

// Send message function
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');

    // Clear input and disable send button
    messageInput.value = '';
    sendButton.disabled = true;
    showLoading(true);

    try {
        // Send message to Flask backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        // Add bot response to chat
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

// Add message to chat
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

// Format message text (handle line breaks, code, etc.)
function formatMessage(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
}

// Handle Enter key press
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Insert command into input field
function insertCommand(command) {
    messageInput.value = command;
    messageInput.focus();
    messageInput.select();
}

// Show/hide loading overlay
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// Scroll to bottom of chat
function scrollToBottom() {
    setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 100);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Focus on input field
    messageInput.focus();

    // Add some example interactions
    setTimeout(() => {
        scrollToBottom();
    }, 500);
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
    scrollToBottom();
});

// Add click-to-copy for code blocks
document.addEventListener('click', (e) => {
    if (e.target.tagName === 'CODE') {
        const text = e.target.textContent;
        navigator.clipboard.writeText(text).then(() => {
            // Show temporary feedback
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

