// DOM Elements Binding
const savingsBalanceEl = document.getElementById('savings-balance');
const checkingBalanceEl = document.getElementById('checking-balance');
const fdAmountEl = document.getElementById('fd-amount');
const fdTenureEl = document.getElementById('fd-tenure');
const fdRateEl = document.getElementById('fd-rate');
const fdMaturityEl = document.getElementById('fd-maturity');
const fdStatusEl = document.getElementById('fd-status');
const transactionsBody = document.getElementById('transactions-body');
const apiStatusEl = document.getElementById('api-status');

// Voice assistant DOM elements
const micBtn = document.getElementById('mic-btn');
const micIcon = document.getElementById('mic-icon');
const micContainer = micBtn.parentElement;
const micHintText = document.getElementById('mic-hint-text');

const userTranscriptBubble = document.getElementById('user-transcript-bubble');
const userTranscriptText = document.getElementById('user-transcript');
const assistantResponseBubble = document.getElementById('assistant-response-bubble');
const assistantResponseText = document.getElementById('assistant-response');

// Authentication DOM elements
const authContainer = document.getElementById('auth-container');
const dashboardContainer = document.getElementById('dashboard-container');
const userProfile = document.getElementById('user-profile');
const loggedUserName = document.getElementById('logged-user-name');
const logoutBtn = document.getElementById('logout-btn');

const tabLoginBtn = document.getElementById('tab-login-btn');
const tabRegisterBtn = document.getElementById('tab-register-btn');
const loginFormPanel = document.getElementById('login-form-panel');
const registerFormPanel = document.getElementById('register-form-panel');

const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');

const voiceLoginBtn = document.getElementById('voice-login-btn');
const voiceLoginMicWrapper = voiceLoginBtn.parentElement;
const voiceLoginStatus = document.getElementById('voice-login-status');

const dictatePassphraseBtn = document.getElementById('dictate-passphrase-btn');

// App Session State variables
let recognition = null;
let activeSpeechMode = 'assistant'; // 'assistant', 'login', 'dictate'
let isRecording = false;
let isVoiceLoginRecording = false;
let isDictateRecording = false;
let currentUser = null; // Session details { username, name }

// Speech Recognition & Synthesis Initialization
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        if (activeSpeechMode === 'assistant') {
            isRecording = true;
            micContainer.classList.add('recording');
            micIcon.className = 'fa-solid fa-square';
            micHintText.textContent = "Listening... Speak now.";
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopSpeechEngine();
        if (activeSpeechMode === 'assistant') {
            micHintText.textContent = `Error: ${event.error}. Try again.`;
        } else if (activeSpeechMode === 'login') {
            voiceLoginStatus.className = 'voice-login-status error';
            voiceLoginStatus.textContent = `Error: ${event.error}`;
        }
    };

    recognition.onend = () => {
        stopSpeechEngine();
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (activeSpeechMode === 'assistant') {
            handleUserSpeech(transcript);
        } else if (activeSpeechMode === 'login') {
            handleVoiceLogin(transcript);
        } else if (activeSpeechMode === 'dictate') {
            handleDictatePassphrase(transcript);
        }
    };
} else {
    micHintText.textContent = "Speech recognition not supported in this browser. Use Chrome/Edge.";
    micBtn.disabled = true;
    micBtn.style.opacity = '0.5';
    voiceLoginBtn.disabled = true;
    voiceLoginBtn.style.opacity = '0.5';
    dictatePassphraseBtn.disabled = true;
    dictatePassphraseBtn.style.opacity = '0.5';
}

function stopSpeechEngine() {
    isRecording = false;
    micContainer.classList.remove('recording');
    micIcon.className = 'fa-solid fa-microphone';
    micHintText.textContent = "Tap the microphone to speak a banking command";

    isVoiceLoginRecording = false;
    voiceLoginMicWrapper.classList.remove('listening');
    if (activeSpeechMode === 'login' && voiceLoginStatus.textContent === "Listening to passphrase...") {
        voiceLoginStatus.textContent = "Tap mic to retry";
    }

    isDictateRecording = false;
    dictatePassphraseBtn.classList.remove('listening');
}

// Speak response out loud using browser TTS
function speakText(text) {
    if (!('speechSynthesis' in window)) return;
    
    const cleanText = text.replace(/\[Simulation Mode\]/g, '').replace(/\[Simulation\]/g, '').trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    const voices = window.speechSynthesis.getVoices();
    const targetVoice = voices.find(voice => 
        voice.lang.includes('en') && (voice.name.includes('Google') || voice.name.includes('Natural') || voice.name.includes('Samantha'))
    );
    if (targetVoice) utterance.voice = targetVoice;

    window.speechSynthesis.speak(utterance);
}

// Fetch voices early
if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
}

// Traditional UI triggers: Tabs navigation
tabLoginBtn.addEventListener('click', () => {
    tabLoginBtn.classList.add('active');
    tabRegisterBtn.classList.remove('active');
    loginFormPanel.classList.remove('hidden');
    registerFormPanel.classList.add('hidden');
});

tabRegisterBtn.addEventListener('click', () => {
    tabRegisterBtn.classList.add('active');
    tabLoginBtn.classList.remove('active');
    registerFormPanel.classList.remove('hidden');
    loginFormPanel.classList.add('hidden');
});

// Credentials Login Form Submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Invalid login credentials.");
            return;
        }

        const data = await response.json();
        if (data.success) {
            loginUser(data.username, data.name);
        }
    } catch (err) {
        console.error(err);
        alert("Server communication error.");
    }
});

// Registration Form Submission
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('register-name').value;
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    const voicePassphrase = document.getElementById('register-passphrase').value;

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                username,
                password,
                voice_passphrase: voicePassphrase
            })
        });

        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Registration failed.");
            return;
        }

        const data = await response.json();
        if (data.success) {
            alert("Account registered successfully!");
            loginUser(data.username, data.name);
        }
    } catch (err) {
        console.error(err);
        alert("Registration server error.");
    }
});

// Logout trigger
logoutBtn.addEventListener('click', () => {
    logoutUser();
});

// Trigger login context UI
function loginUser(username, name) {
    currentUser = { username, name };
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    // Toggle container views
    authContainer.classList.add('hidden');
    dashboardContainer.classList.remove('hidden');
    userProfile.classList.remove('hidden');
    loggedUserName.textContent = name;

    // Load initial user state
    fetchInitialState(username);

    // Speak welcome message
    speakText(`Welcome to Finova Bank, ${name}! How can I help you today?`);
}

function logoutUser() {
    window.speechSynthesis.cancel();
    localStorage.removeItem('currentUser');
    currentUser = null;
    window.location.reload();
}

// Speech Actions orchestration

// 1. Voice login mic trigger
voiceLoginBtn.addEventListener('click', () => {
    if (!recognition) return;
    if (isVoiceLoginRecording) {
        recognition.stop();
    } else {
        window.speechSynthesis.cancel();
        activeSpeechMode = 'login';
        isVoiceLoginRecording = true;
        voiceLoginMicWrapper.classList.add('listening');
        voiceLoginStatus.className = 'voice-login-status';
        voiceLoginStatus.textContent = "Listening to passphrase...";
        recognition.start();
    }
});

// Handle matched voice login transcription
async function handleVoiceLogin(text) {
    if (!text || text.trim() === '') return;
    voiceLoginStatus.textContent = `Checking phrase...`;

    try {
        const response = await fetch('/api/voice-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ passphrase: text })
        });
        
        const data = await response.json();
        if (data.success) {
            voiceLoginStatus.className = 'voice-login-status';
            voiceLoginStatus.textContent = "Welcome back!";
            setTimeout(() => {
                loginUser(data.username, data.name);
            }, 500);
        } else {
            voiceLoginStatus.className = 'voice-login-status error';
            voiceLoginStatus.textContent = "Voice passphrase not matched.";
            speakText("Access denied. Voice print not recognized.");
        }
    } catch (err) {
        console.error(err);
        voiceLoginStatus.className = 'voice-login-status error';
        voiceLoginStatus.textContent = "Auth server offline.";
    }
}

// 2. Dictate voice passphrase in Registration
dictatePassphraseBtn.addEventListener('click', () => {
    if (!recognition) return;
    if (isDictateRecording) {
        recognition.stop();
    } else {
        window.speechSynthesis.cancel();
        activeSpeechMode = 'dictate';
        isDictateRecording = true;
        dictatePassphraseBtn.classList.add('listening');
        recognition.start();
    }
});

function handleDictatePassphrase(text) {
    if (!text || text.trim() === '') return;
    const phrase = text.replace(/[.!?]/g, '').trim().toLowerCase();
    document.getElementById('register-passphrase').value = phrase;
    speakText(`Recorded: ${phrase}`);
}

// 3. Main Voice assistant trigger
micBtn.addEventListener('click', () => {
    if (!recognition) return;
    
    if (isRecording) {
        recognition.stop();
    } else {
        window.speechSynthesis.cancel();
        activeSpeechMode = 'assistant';
        try {
            recognition.start();
        } catch (e) {
            console.error(e);
        }
    }
});

// Bind tags suggestion click behaviors
document.querySelectorAll('.suggest-tag').forEach(tag => {
    tag.addEventListener('click', () => {
        const text = tag.textContent.replace(/"/g, '');
        handleUserSpeech(text);
    });
});

// Communicate voice speech inputs to the chat server
async function handleUserSpeech(text) {
    if (!text || text.trim() === '' || !currentUser) return;

    userTranscriptBubble.classList.remove('hidden');
    userTranscriptText.textContent = text;

    assistantResponseBubble.classList.remove('hidden');
    assistantResponseText.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Checking ledger...';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: text,
                username: currentUser.username
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        // Render speech result
        assistantResponseText.textContent = data.response;
        updateDashboard(data.state);
        speakText(data.response);

    } catch (error) {
        console.error('API Error:', error);
        assistantResponseText.textContent = "Error communicating with Finova ledger service.";
        speakText("I encountered an error communicating with the banking server.");
    }
}

// Update the visual dashboard cards
function updateDashboard(state) {
    if (!state) return;

    updateValueWithAnimation(savingsBalanceEl, `$${state.balances.savings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
    updateValueWithAnimation(checkingBalanceEl, `$${state.balances.checking.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);

    if (state.fixed_deposits && state.fixed_deposits.length > 0) {
        const fd = state.fixed_deposits[0];
        updateValueWithAnimation(fdAmountEl, `$${fd.principal_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`);
        updateValueWithAnimation(fdTenureEl, fd.tenure);
        updateValueWithAnimation(fdRateEl, fd.interest_rate);
        updateValueWithAnimation(fdMaturityEl, fd.maturity_date);
        updateValueWithAnimation(fdStatusEl, fd.status);
        document.getElementById('fd-container').style.display = 'block';
    } else {
        // If user doesn't have an FD, hide/clear card metrics
        fdAmountEl.textContent = "$0.00";
        fdTenureEl.textContent = "-";
        fdRateEl.textContent = "-";
        fdMaturityEl.textContent = "-";
        fdStatusEl.textContent = "-";
    }

    transactionsBody.innerHTML = '';
    state.transactions.forEach(tx => {
        const row = document.createElement('tr');
        const amountClass = tx.type.toLowerCase() === 'credit' ? 'credit' : 'debit';
        const sign = tx.type.toLowerCase() === 'credit' ? '+' : '-';
        
        row.innerHTML = `
            <td>${tx.date}</td>
            <td><strong>${tx.description}</strong></td>
            <td>${tx.category}</td>
            <td><span class="tx-type-badge ${amountClass}">${tx.type}</span></td>
            <td class="text-right tx-amount ${amountClass}">${sign}$${tx.amount.toFixed(2)}</td>
        `;
        transactionsBody.appendChild(row);
    });
}

function updateValueWithAnimation(element, newValue) {
    if (element.textContent !== newValue) {
        element.textContent = newValue;
        const cardParent = element.closest('.card');
        if (cardParent) {
            cardParent.classList.remove('flash-update');
            void cardParent.offsetWidth;
            cardParent.classList.add('flash-update');
        }
    }
}

// Load initial state for specific user session
async function fetchInitialState(username) {
    try {
        const response = await fetch(`/api/state?username=${encodeURIComponent(username)}`);
        if (response.ok) {
            const state = await response.json();
            updateDashboard(state);
            
            apiStatusEl.className = "api-status connected";
            apiStatusEl.querySelector('.status-text').textContent = "Online";
        }
    } catch (error) {
        console.error("Could not reach backend:", error);
        apiStatusEl.className = "api-status";
        apiStatusEl.querySelector('.status-text').textContent = "Offline";
    }
}

// App Startup Orchestration
window.addEventListener('DOMContentLoaded', () => {
    const session = localStorage.getItem('currentUser');
    if (session) {
        currentUser = JSON.parse(session);
        loginUser(currentUser.username, currentUser.name);
    } else {
        // Show auth, hide dashboard
        authContainer.classList.remove('hidden');
        dashboardContainer.classList.add('hidden');
        userProfile.classList.add('hidden');
        
        // Query ping to check API connection
        fetch('/api/state?username=alice')
            .then(res => {
                if (res.ok) {
                    apiStatusEl.className = "api-status connected";
                    apiStatusEl.querySelector('.status-text').textContent = "Online";
                }
            })
            .catch(() => {
                apiStatusEl.className = "api-status";
                apiStatusEl.querySelector('.status-text').textContent = "Offline";
            });
    }
});
