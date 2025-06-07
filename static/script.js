document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const emotionBtn = document.getElementById('emotion-btn');
    const voiceButton = document.getElementById('voice-btn');
    const chatMessages = document.getElementById('chat-messages');
    const newChatBtn = document.getElementById('new-chat');
    const conversationList = document.getElementById('conversation-list');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.querySelector('.close-btn');
    const clearChatBtn = document.getElementById('clear-chat');
    const exportChatBtn = document.getElementById('export-chat');
    const quickOptions = document.querySelectorAll('.quick-option');
    const emotionQuickBtn = document.getElementById('emotion-quick-btn');
    const voiceQuickBtn = document.getElementById('voice-quick-btn');
    const themeSelect = document.getElementById('theme-select');
    const voiceSpeed = document.getElementById('voice-speed');
    const historyLimit = document.getElementById('history-limit');
    
    let currentSessionId = generateSessionId();
    let isListening = false;

    // Generate a unique session ID
    function generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    // Load conversation history
    async function loadConversation(sessionId) {
        try {
            const response = await fetch(`/conversation/${sessionId}`);
            const data = await response.json();
            
            if (data.messages) {
                chatMessages.innerHTML = '';
                data.messages.forEach(msg => {
                    addMessage(msg.content, msg.role);
                });
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            addMessage('Error loading conversation history. Please try again.', 'assistant');
        }
    }

    // Add message to chat
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">
                ${formatMessage(message)}
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Send message
    async function sendMessage(message) {
        if (!message.trim()) return;
        
        addMessage(message, 'user');
        messageInput.value = '';
        messageInput.style.height = 'auto';

        try {
            const response = await fetch('/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message.trim(),
                    session_id: currentSessionId
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.error) {
                addMessage(data.error, 'assistant');
            } else {
                addMessage(data.response, 'assistant');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your message. Please try again.', 'assistant');
        }
    }

    // Start new chat
    function startNewChat() {
        currentSessionId = generateSessionId();
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to AI Mental Wellness Assistant</h2>
                <p>I'm here to help you with your mental well-being. How can I assist you today?</p>
                <div class="quick-start">
                    <h3>Quick Start</h3>
                    <div class="quick-start-options">
                        <button class="quick-option" data-prompt="How are you feeling today?">
                            <i class="fas fa-heart"></i>
                            Check-in
                        </button>
                        <button class="quick-option" data-prompt="I'm feeling stressed">
                            <i class="fas fa-brain"></i>
                            Stress Relief
                        </button>
                        <button class="quick-option" data-prompt="I need motivation">
                            <i class="fas fa-star"></i>
                            Motivation
                        </button>
                    </div>
                </div>
            </div>
        `;
        addConversationToList(currentSessionId);
    }

    // Add conversation to sidebar
    function addConversationToList(sessionId) {
        const conversationDiv = document.createElement('div');
        conversationDiv.classList.add('conversation-item');
        const timestamp = new Date(parseInt(sessionId.split('_')[1])).toLocaleString();
        conversationDiv.textContent = `Chat ${timestamp}`;
        conversationDiv.onclick = () => {
            currentSessionId = sessionId;
            loadConversation(sessionId);
        };
        conversationList.appendChild(conversationDiv);
    }

    // Detect emotion
    async function detectEmotion() {
        try {
            emotionBtn.disabled = true;
            emotionBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
            
            const response = await fetch('/detect-emotion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: currentSessionId })
            });
            
            const data = await response.json();
            
            if (data.error) {
                addMessage(data.error, 'assistant');
            } else {
                addMessage(`Detected emotion: ${data.emotion}`, 'assistant');
                addMessage(data.response, 'assistant');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error detecting your emotion. Please try again.', 'assistant');
        } finally {
            emotionBtn.disabled = false;
            emotionBtn.innerHTML = '<i class="fas fa-smile"></i> Detect Emotion';
        }
    }

    // Voice recognition
    async function startVoiceRecognition() {
        if (isListening) return;
        
        isListening = true;
        voiceButton.innerHTML = '<i class="fas fa-microphone-alt"></i> Listening...';
        
        try {
            const response = await fetch('/voice-recognition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ session_id: currentSessionId })
            });

            if (!response.ok) {
                throw new Error('Voice recognition failed');
            }

            const data = await response.json();
            
            if (data.text) {
                messageInput.value = data.text;
                sendMessage(data.text);
            } else if (data.error) {
                addMessage(data.error, 'assistant');
            }
        } catch (error) {
            console.error('Error:', error);
            addMessage('Sorry, there was an error with voice recognition. Please try again.', 'assistant');
        } finally {
            isListening = false;
            voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
        }
    }

    // Auto-resize textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = messageInput.scrollHeight + 'px';
    });

    // Event Listeners
    sendButton.addEventListener('click', () => {
        const message = messageInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    });

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendButton.click();
        }
    });

    emotionBtn.addEventListener('click', detectEmotion);
    emotionQuickBtn.addEventListener('click', detectEmotion);
    voiceButton.addEventListener('click', startVoiceRecognition);
    voiceQuickBtn.addEventListener('click', startVoiceRecognition);
    newChatBtn.addEventListener('click', startNewChat);
    settingsBtn.addEventListener('click', openSettings);
    closeSettingsBtn.addEventListener('click', closeSettings);
    clearChatBtn.addEventListener('click', clearChat);
    exportChatBtn.addEventListener('click', exportChat);

    // Quick start options
    quickOptions.forEach(option => {
        option.addEventListener('click', () => {
            const prompt = option.getAttribute('data-prompt');
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    // Settings Management
    function openSettings() {
        settingsModal.style.display = 'block';
        loadSettings();
    }

    function closeSettings() {
        settingsModal.style.display = 'none';
    }

    function loadSettings() {
        const settings = JSON.parse(localStorage.getItem('settings') || '{}');
        
        // Load theme
        themeSelect.value = settings.theme || 'dark';
        applyTheme(settings.theme || 'dark');
        
        // Load voice settings
        voiceSpeed.value = settings.voiceSpeed || '1';
        
        // Load chat settings
        historyLimit.value = settings.messageHistory || '10';
    }

    function saveSettings() {
        const settings = {
            theme: themeSelect.value,
            voiceSpeed: voiceSpeed.value,
            messageHistory: historyLimit.value
        };
        
        localStorage.setItem('settings', JSON.stringify(settings));
        applyTheme(settings.theme);
    }

    function applyTheme(theme) {
        document.body.className = theme;
    }

    // Chat Management
    function clearChat() {
        if (confirm('Are you sure you want to clear this chat?')) {
            chatMessages.innerHTML = '';
            startNewChat();
        }
    }

    function exportChat() {
        const messages = Array.from(chatMessages.querySelectorAll('.message')).map(msg => {
            const sender = msg.classList.contains('user-message') ? 'User' : 'Assistant';
            const content = msg.querySelector('.message-content').textContent;
            return `${sender}: ${content}`;
        }).join('\n\n');

        const blob = new Blob([messages], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_export_${currentSessionId}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Settings changes
    themeSelect.addEventListener('change', () => {
        saveSettings();
    });

    voiceSpeed.addEventListener('change', () => {
        saveSettings();
    });

    historyLimit.addEventListener('change', () => {
        saveSettings();
    });

    // Close settings modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            closeSettings();
        }
    });

    // Initialize
    startNewChat();
    loadSettings();

    // Navigation handling
    function startChat() {
        window.location.href = '/chat';
    }

    // Smooth scrolling for anchor links
    document.addEventListener('DOMContentLoaded', function() {
        const anchorLinks = document.querySelectorAll('a[href^="#"]');
        
        anchorLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    });
});

function formatMessage(text) {
    // Convert URLs to clickable links
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    // Convert newlines to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
} 