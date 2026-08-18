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

// Visibility state for account balances
const balancesVisible = {
    'savings-balance': false,
    'checking-balance': false,
    'fd-amount': false
};

// Voice assistant DOM elements
const micBtn = document.getElementById('mic-btn');
const micIcon = document.getElementById('mic-icon');
const micContainer = micBtn.parentElement;
const micHintText = document.getElementById('mic-hint-text');

const chatDisplay = document.getElementById('chat-display');

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

// Face Recognition DOM Elements
const faceLoginUsername = document.getElementById('face-login-username');
const faceLoginCameraContainer = document.getElementById('face-login-camera-container');
const faceLoginVideo = document.getElementById('face-login-video');
const faceLoginCanvas = document.getElementById('face-login-canvas');
const faceLoginCameraToggleBtn = document.getElementById('face-login-camera-toggle-btn');
const faceLoginCaptureBtn = document.getElementById('face-login-capture-btn');
const faceLoginStatus = document.getElementById('face-login-status');

const faceRegisterCameraContainer = document.getElementById('face-register-camera-container');
const faceRegisterVideo = document.getElementById('face-register-video');
const faceRegisterCanvas = document.getElementById('face-register-canvas');
const faceRegisterCameraToggleBtn = document.getElementById('face-register-camera-toggle-btn');
const faceRegisterCaptureBtn = document.getElementById('face-register-capture-btn');
const faceRegisterStatus = document.getElementById('face-register-status');

let faceLoginStream = null;
let faceRegisterStream = null;
let capturedFaceBase64 = null; // Holds the base64 face snapshot for registration


// MPIN secure entry UI elements
const mpinInputWrapper = document.getElementById('mpin-input-wrapper');
const typeMpinInput = document.getElementById('type-mpin-input');
const mpinSubmitBtn = document.getElementById('mpin-submit-btn');
const mpinCancelBtn = document.getElementById('mpin-cancel-btn');

// PDF Statement Modal elements
const statementModal = document.getElementById('statement-modal');
const statementModalBtn = document.getElementById('statement-modal-btn');
const closeStatementModalBtn = document.getElementById('close-statement-modal');
const cancelStatementBtn = document.getElementById('cancel-statement-btn');
const statementForm = document.getElementById('statement-form');
const dateRangeInputs = document.getElementById('date-range-inputs');
const statementStartDate = document.getElementById('statement-start-date');
const statementEndDate = document.getElementById('statement-end-date');

// App Session State variables
let recognition = null;
let activeSpeechMode = 'assistant'; // 'assistant', 'login', 'dictate', 'voice2fa', 'dictate_reset_voice'
let isRecording = false;
let isVoiceLoginRecording = false;
let isDictateRecording = false;
let isVoice2FARecording = false;
let isResetVoiceRecording = false;
let pending2FAUser = null;
let currentUser = null; // Session details { username, name }

let selectedLanguage = localStorage.getItem('appLanguage') || 'en-IN';

// Dictionary mapping selector query to translation key
const elementSelectors = {
    '#tab-login-btn': 'tab-login-btn',
    '#tab-register-btn': 'tab-register-btn',
    'label[for="login-username"]': 'login-username-label',
    'label[for="login-password"]': 'login-password-label',
    '#login-form .auth-submit-btn': 'login-btn-text',
    '.voice-login-section h4': 'voice-login-title',
    '.voice-login-hint': 'voice-login-hint',
    'label[for="voice-login-username"]': 'voice-username-label',
    'label[for="register-name"]': 'register-name-label',
    'label[for="register-username"]': 'register-username-label',
    'label[for="register-password"]': 'register-password-label',
    'label[for="register-mpin"]': 'register-mpin-label',
    'label[for="register-passphrase"]': 'register-passphrase-label',
    'label[for="register-question"]': 'register-question-label',
    'label[for="register-answer"]': 'register-answer-label',
    '#register-form .auth-submit-btn': 'register-btn-text',
    '.balance-card .card-header h2': 'dashboard-balances-title',
    '.balance-item:nth-child(1) .balance-label': 'dashboard-savings-label',
    '.balance-item:nth-child(2) .balance-label': 'dashboard-checking-label',
    '.fd-card .card-header h2': 'dashboard-fd-title',
    '.fd-main-details .fd-label': 'dashboard-fd-principal-label',
    '.fd-details-grid .fd-detail:nth-child(1) .fd-detail-label': 'dashboard-fd-tenure-label',
    '.fd-details-grid .fd-detail:nth-child(2) .fd-detail-label': 'dashboard-fd-rate-label',
    '.fd-details-grid .fd-detail:nth-child(3) .fd-detail-label': 'dashboard-fd-maturity-label',
    '.fd-details-grid .fd-detail:nth-child(4) .fd-detail-label': 'dashboard-fd-status-label',
    '.transfer-card .card-header h2': 'dashboard-transfer-title',
    'label[for="payment-recipient"]': 'dashboard-transfer-recipient',
    'label[for="payment-source"]': 'dashboard-transfer-source',
    'label[for="payment-amount"]': 'dashboard-transfer-amount',
    'label[for="payment-mpin"]': 'dashboard-transfer-mpin',
    '.history-card .card-header h2': 'dashboard-history-title',
    '#payment-recipient option[value=""]': 'option-select-recipient',
    '#payment-source option[value="savings"]': 'option-savings',
    '#payment-source option[value="checking"]': 'option-checking',
    '#register-question option[value=""]': 'option-select-question',
    '#dashboard-payment-form button[type="submit"]': 'dashboard-transfer-btn-text',
    '#text-tab-dashboard': 'tab-dashboard',
    '#text-tab-analytics': 'tab-analytics',
    '#text-tab-voice': 'tab-voice',
    '#text-tab-knowledge': 'tab-knowledge',
    '#lbl-voice-mic-header': 'voice-mic-header',
    '#lbl-voice-transactions-title': 'voice-transactions-title',
    '#lbl-filter-duration': 'filter-duration',
    '#lbl-filter-category': 'filter-category',
    '#lbl-filter-type': 'filter-type',
    '#lbl-metric-income': 'metric-income',
    '#lbl-metric-expense': 'metric-expense',
    '#lbl-metric-savings': 'metric-savings',
    '#lbl-metric-count': 'metric-count',
    '#lbl-chart-spending-trend': 'chart-spending-trend',
    '#lbl-chart-spending-category': 'chart-spending-category',
    '#lbl-chart-income-vs-expense': 'chart-income-vs-expense',
    '#lbl-k-card-title1': 'k-card-title1',
    '#lbl-k-card-desc1': 'k-card-desc1',
    '#lbl-k-card-title2': 'k-card-title2',
    '#lbl-k-card-desc2': 'k-card-desc2',
    '#lbl-k-card-title3': 'k-card-title3',
    '#lbl-k-card-desc3': 'k-card-desc3',
    '#lbl-k-prompts-title': 'k-prompts-title',
    '#lbl-k-prompts-intro': 'k-prompts-intro',
    '#lbl-k-cat-account': 'k-cat-account',
    '#lbl-k-cat-transfer': 'k-cat-transfer',
    '#lbl-k-cat-fd': 'k-cat-fd',
    '#lbl-k-cat-multilingual': 'k-cat-multilingual',
    '#btn-k-prompt-sbal': 'btn-k-prompt-sbal',
    '#btn-k-prompt-ledger': 'btn-k-prompt-ledger',
    '#btn-k-prompt-cbal': 'btn-k-prompt-cbal',
    '#btn-k-prompt-send-alice': 'btn-k-prompt-send-alice',
    '#btn-k-prompt-send-bob': 'btn-k-prompt-send-bob',
    '#btn-k-prompt-fd-details': 'btn-k-prompt-fd-details',
    '#btn-k-prompt-fd-rates': 'btn-k-prompt-fd-rates',
    '#lbl-k-support-title': 'k-support-title',
    '#lbl-k-support-intro': 'k-support-intro',
    '#lbl-k-query-label': 'k-query-label',
    '#btn-k-submit': 'btn-k-submit',
    '#lbl-k-response-title': 'lbl-k-response-title',
    '#lbl-th-date1': 'th-date',
    '#lbl-th-desc1': 'th-desc',
    '#lbl-th-cat1': 'th-cat',
    '#lbl-th-type1': 'th-type',
    '#lbl-th-amount1': 'th-amount',
    '#lbl-th-date2': 'th-date',
    '#lbl-th-desc2': 'th-desc',
    '#lbl-th-cat2': 'th-cat',
    '#lbl-th-type2': 'th-type',
    '#lbl-th-amount2': 'th-amount'
};

const placeholderSelectors = {
    '#login-username': 'placeholder-login-username',
    '#login-password': 'placeholder-login-password',
    '#voice-login-username': 'placeholder-voice-login-username',
    '#register-name': 'placeholder-register-name',
    '#register-username': 'placeholder-register-username',
    '#register-password': 'placeholder-register-password',
    '#register-mpin': 'placeholder-register-mpin',
    '#register-passphrase': 'placeholder-register-passphrase',
    '#register-answer': 'placeholder-register-answer',
    '#reset-username': 'placeholder-reset-username',
    '#reset-answer': 'placeholder-reset-answer',
    '#reset-new-password': 'placeholder-reset-new-password',
    '#reset-voice-answer': 'placeholder-reset-voice-answer',
    '#reset-voice-passphrase': 'placeholder-reset-voice-passphrase',
    '#k-query-input': 'placeholder-k-query-input'
};

const translations = {
    'en-IN': {
        'tab-login-btn': 'Secure Login',
        'tab-register-btn': 'Create Account',
        'login-username-label': '<i class="fa-solid fa-user"></i> Username',
        'login-password-label': '<i class="fa-solid fa-lock"></i> Password',
        'login-btn-text': 'Access Accounts',
        'voice-login-title': 'Voice Passphrase Login',
        'voice-login-hint': 'Enter username and tap mic to speak your passphrase',
        'voice-username-label': '<i class="fa-solid fa-user-tag"></i> Username (Optional)',
        'register-name-label': '<i class="fa-solid fa-signature"></i> Full Name',
        'register-username-label': '<i class="fa-solid fa-circle-user"></i> Choose Username',
        'register-password-label': '<i class="fa-solid fa-key"></i> Choose Password',
        'register-mpin-label': '<i class="fa-solid fa-shield-halved"></i> Set MPIN (4 Digits)',
        'register-passphrase-label': '<i class="fa-solid fa-microphone-lines"></i> Voice Passphrase',
        'register-question-label': '<i class="fa-solid fa-circle-question"></i> Security Question',
        'register-answer-label': '<i class="fa-solid fa-pen"></i> Security Answer',
        'register-btn-text': 'Register Account',
        'dashboard-balances-title': 'Account Balances',
        'dashboard-savings-label': 'Savings Account',
        'dashboard-checking-label': 'Current Account',
        'dashboard-fd-title': 'Recent Fixed Deposit',
        'dashboard-fd-principal-label': 'Principal Amount',
        'dashboard-fd-tenure-label': 'Tenure',
        'dashboard-fd-rate-label': 'Interest Rate',
        'dashboard-fd-maturity-label': 'Maturity Date',
        'dashboard-fd-status-label': 'Status',
        'dashboard-transfer-title': 'Quick Transfer',
        'dashboard-transfer-recipient': '<i class="fa-solid fa-user"></i> Recipient',
        'dashboard-transfer-source': '<i class="fa-solid fa-wallet"></i> Pay From',
        'dashboard-transfer-amount': '<i class="fa-solid fa-indian-rupee-sign"></i> Amount',
        'dashboard-transfer-mpin': '<i class="fa-solid fa-lock"></i> 4-Digit MPIN',
        'dashboard-history-title': 'Recent Transactions',
        'dashboard-transfer-btn-text': '<i class="fa-solid fa-paper-plane"></i> Send Payment',
        'mic-hint-ready': 'Tap the microphone to speak a banking command',
        'mic-hint-listening': 'Listening... Speak now.',
        'placeholder-login-username': 'Enter username (e.g. alice)',
        'placeholder-login-password': 'Enter password (e.g. password123)',
        'placeholder-voice-login-username': 'Enter username (e.g. alice)',
        'placeholder-register-name': 'Enter full name',
        'placeholder-register-username': 'Choose a unique username',
        'placeholder-register-password': 'Choose password',
        'placeholder-register-mpin': 'Enter 4-digit PIN',
        'placeholder-register-passphrase': 'e.g. open sesame',
        'placeholder-register-answer': 'Enter your answer',
        'placeholder-reset-username': 'Enter username (e.g. alice)',
        'placeholder-reset-answer': 'Enter your answer',
        'placeholder-reset-new-password': 'Enter new password',
        'placeholder-reset-voice-answer': 'Enter your answer',
        'placeholder-reset-voice-passphrase': 'Type or tap mic to speak passphrase',
        'option-select-recipient': 'Select Recipient',
        'option-savings': 'Savings',
        'option-checking': 'Current',
        'option-select-question': 'Select a security question',
        'tab-dashboard': 'Dashboard',
        'tab-analytics': 'Analytics & Insights',
        'filter-duration': 'Duration',
        'filter-category': 'Category',
        'filter-type': 'Transaction Type',
        'metric-income': 'Total Income',
        'metric-expense': 'Total Spending',
        'metric-savings': 'Net Savings',
        'metric-count': 'Transactions',
        'chart-spending-trend': 'Spending Trend Over Time',
        'chart-spending-category': 'Spending by Category',
        'chart-income-vs-expense': 'Income vs Expenses Comparison',
        'tab-voice': 'Voice Transaction',
        'tab-knowledge': 'Knowledge Base',
        'voice-mic-header': 'Voice Control',
        'voice-transactions-title': 'Voice Transactions Ledger',
        'k-card-title1': 'Transaction Security',
        'k-card-desc1': 'All payments require your unique 4-digit MPIN. Never share your MPIN or passwords with anyone. To add a layer of safety, register your unique voice biometric print.',
        'k-card-title2': 'Limits & Rules',
        'k-card-desc2': 'Savings accounts have a daily voice transfer limit of ₹50,000. Fixed deposit interest rates range from 6.5% to 7.8% depending on the lock-in tenure.',
        'k-card-title3': 'Voice Commands Guide',
        'k-card-desc3': 'NidhiVani AI uses advanced LangGraph routing to parse natural spoken commands. Try speaking in English, Hindi, or Marathi directly.',
        'k-prompts-title': 'Example Voice Prompts',
        'k-prompts-intro': 'Click on any of the example commands below to try it out in the Voice Assistant panel:',
        'k-cat-account': 'Account & Balance',
        'k-cat-transfer': 'Money Transfers',
        'k-cat-fd': 'Fixed Deposits',
        'k-cat-multilingual': 'Multilingual Examples',
        'btn-k-prompt-sbal': '"What is my savings account balance?"',
        'btn-k-prompt-ledger': '"Show my recent transaction ledger"',
        'btn-k-prompt-cbal': '"Check my Current account balance"',
        'btn-k-prompt-send-alice': '"Send ₹200 to Alice Smith from savings"',
        'btn-k-prompt-send-bob': '"Transfer ₹1500 to Bob Jones from Current"',
        'btn-k-prompt-fd-details': '"Show my fixed deposit details"',
        'btn-k-prompt-fd-rates': '"What are the latest FD interest rates?"',
        'k-support-title': 'Support Desk',
        'k-support-intro': 'Have questions about interest rates, banking policies, or branch hours? Ask our support specialist below:',
        'k-query-label': '<i class="fa-solid fa-pen"></i> Type your question',
        'btn-k-submit': '<i class="fa-solid fa-paper-plane"></i> Submit Inquiry',
        'lbl-k-response-title': 'Support Specialist Response:',
        'placeholder-k-query-input': 'e.g. What are the branch timings? Do you offer loans?',
        'th-date': 'Date',
        'th-desc': 'Description',
        'th-cat': 'Category',
        'th-type': 'Type',
        'th-amount': 'Amount'
    },
    'hi-IN': {
        'tab-login-btn': 'सुरक्षित लॉगिन',
        'tab-register-btn': 'खाता बनाएं',
        'login-username-label': '<i class="fa-solid fa-user"></i> उपयोगकर्ता नाम (Username)',
        'login-password-label': '<i class="fa-solid fa-lock"></i> पासवर्ड',
        'login-btn-text': 'खाता एक्सेस करें',
        'voice-login-title': 'आवाज पासफ़्रेज़ लॉगिन',
        'voice-login-hint': 'उपयोगकर्ता नाम दर्ज करें और पासफ़्रेज़ बोलने के लिए माइक दबाएं',
        'voice-username-label': '<i class="fa-solid fa-user-tag"></i> उपयोगकर्ता नाम (वैकल्पिक)',
        'register-name-label': '<i class="fa-solid fa-signature"></i> पूरा नाम',
        'register-username-label': '<i class="fa-solid fa-circle-user"></i> उपयोगकर्ता नाम चुनें',
        'register-password-label': '<i class="fa-solid fa-key"></i> पासवर्ड चुनें',
        'register-mpin-label': '<i class="fa-solid fa-shield-halved"></i> एमपीआईएन सेट करें (4 अंक)',
        'register-passphrase-label': '<i class="fa-solid fa-microphone-lines"></i> आवाज पासफ़्रेज़',
        'register-question-label': '<i class="fa-solid fa-circle-question"></i> सुरक्षा प्रश्न',
        'register-answer-label': '<i class="fa-solid fa-pen"></i> सुरक्षा उत्तर',
        'register-btn-text': 'खाता पंजीकृत करें',
        'dashboard-balances-title': 'खाता शेष (Balances)',
        'dashboard-savings-label': 'बचत खाता (Savings)',
        'dashboard-checking-label': 'चालू खाता (Current)',
        'dashboard-fd-title': 'हालिया सावधि जमा (FD)',
        'dashboard-fd-principal-label': 'मूलधन राशि',
        'dashboard-fd-tenure-label': 'अवधि (Tenure)',
        'dashboard-fd-rate-label': 'ब्याज दर',
        'dashboard-fd-maturity-label': 'परिपक्वता तिथि',
        'dashboard-fd-status-label': 'स्थिति (Status)',
        'dashboard-transfer-title': 'त्वरित हस्तांतरण',
        'dashboard-transfer-recipient': '<i class="fa-solid fa-user"></i> प्राप्तकर्ता',
        'dashboard-transfer-source': '<i class="fa-solid fa-wallet"></i> भुगतान खाता',
        'dashboard-transfer-amount': '<i class="fa-solid fa-indian-rupee-sign"></i> राशि (Amount)',
        'dashboard-transfer-mpin': '<i class="fa-solid fa-lock"></i> 4-अंकीय एमपीआईएन',
        'dashboard-history-title': 'हाल के लेन-देन',
        'dashboard-transfer-btn-text': '<i class="fa-solid fa-paper-plane"></i> भुगतान भेजें',
        'mic-hint-ready': 'बैंकिंग कमांड बोलने के लिए माइक्रोफ़ोन दबाएं',
        'mic-hint-listening': 'सुन रहा हूँ... अब बोलें.',
        'placeholder-login-username': 'उपयोगकर्ता नाम दर्ज करें (उदा. alice)',
        'placeholder-login-password': 'पासवर्ड दर्ज करें (उदा. password123)',
        'placeholder-voice-login-username': 'उपयोगकर्ता नाम दर्ज करें (उदा. alice)',
        'placeholder-register-name': 'पूरा नाम दर्ज करें',
        'placeholder-register-username': 'अनोखा उपयोगकर्ता नाम चुनें',
        'placeholder-register-password': 'पासवर्ड चुनें',
        'placeholder-register-mpin': '4-अंकीय पिन दर्ज करें',
        'placeholder-register-passphrase': 'उदा. open sesame',
        'placeholder-register-answer': 'अपना उत्तर दर्ज करें',
        'placeholder-reset-username': 'उपयोगकर्ता नाम दर्ज करें (उदा. alice)',
        'placeholder-reset-answer': 'अपना उत्तर दर्ज करें',
        'placeholder-reset-new-password': 'नया पासवर्ड दर्ज करें',
        'placeholder-reset-voice-answer': 'अपना उत्तर दर्ज करें',
        'placeholder-reset-voice-passphrase': 'पासफ़्रेज़ टाइप करें या माइक दबाकर बोलें',
        'option-select-recipient': 'प्राप्तकर्ता चुनें',
        'option-savings': 'बचत (Savings)',
        'option-checking': 'चालू (Current)',
        'option-select-question': 'सुरक्षा प्रश्न चुनें',
        'tab-dashboard': 'डैशबोर्ड',
        'tab-analytics': 'विश्लेषण और अंतर्दृष्टि',
        'filter-duration': 'अवधि',
        'filter-category': 'श्रेणी',
        'filter-type': 'लेन-देन प्रकार',
        'metric-income': 'कुल आय',
        'metric-expense': 'कुल खर्च',
        'metric-savings': 'शुद्ध बचत',
        'metric-count': 'लेन-देन',
        'chart-spending-trend': 'समय के साथ खर्च का चलन',
        'chart-spending-category': 'श्रेणी के अनुसार खर्च',
        'chart-income-vs-expense': 'आय बनाम खर्च तुलना',
        'tab-voice': 'आवाज लेनदेन',
        'tab-knowledge': 'ज्ञान केंद्र',
        'voice-mic-header': 'आवाज नियंत्रण',
        'voice-transactions-title': 'आवाज लेनदेन बही',
        'k-card-title1': 'लेन-देन सुरक्षा',
        'k-card-desc1': 'सभी भुगतानों के लिए आपके अद्वितीय 4-अंकीय एमपीआईएन की आवश्यकता होती है। अपना एमपीआईएन या पासवर्ड कभी किसी के साथ साझा न करें। सुरक्षा की एक परत जोड़ने के लिए, अपना अनूठा वॉयस बायोमेट्रिक प्रिंट पंजीकृत करें।',
        'k-card-title2': 'सीमाएं और नियम',
        'k-card-desc2': 'बचत खातों में दैनिक वॉयस ट्रांसफर सीमा ₹50,000 है। लॉक-इन अवधि के आधार पर सावधि जमा ब्याज दरें 6.5% से 7.8% तक होती हैं।',
        'k-card-title3': 'आवाज कमांड गाइड',
        'k-card-desc3': 'निधिवानी एआई प्राकृतिक बोली जाने वाली कमांड को पार्स करने के लिए उन्नत लैनग्राफ रूटिंग का उपयोग करता है। सीधे अंग्रेजी, हिंदी या मराठी में बोलने का प्रयास करें।',
        'k-prompts-title': 'उदाहरण वॉयस प्रॉम्प्ट',
        'k-prompts-intro': 'वॉयस असिस्टेंट पैनल में इसे आज़माने के लिए नीचे दिए गए किसी भी उदाहरण कमांड पर क्लिक करें:',
        'k-cat-account': 'खाता और शेष राशि',
        'k-cat-transfer': 'पैसे ट्रांसफर',
        'k-cat-fd': 'सावधि जमा',
        'k-cat-multilingual': 'बहुभाषी उदाहरण',
        'btn-k-prompt-sbal': '"मेरे बचत खाते का बैलेंस बताओ"',
        'btn-k-prompt-ledger': '"मेरा हालिया लेनदेन बही दिखाओ"',
        'btn-k-prompt-cbal': '"मेरे चालू खाते का बैलेंस जांचें"',
        'btn-k-prompt-send-alice': '"बचत से एलिस स्मिथ को ₹200 भेजें"',
        'btn-k-prompt-send-bob': '"चालू से बॉब जोन्स को ₹1500 ट्रांसफर करें"',
        'btn-k-prompt-fd-details': '"मेरे सावधि जमा विवरण दिखाएं"',
        'btn-k-prompt-fd-rates': '"नवीनतम एफडी ब्याज दरें क्या हैं?"',
        'k-support-title': 'सहायता डेस्क',
        'k-support-intro': 'ब्याज दरों, बैंकिंग नीतियों, या शाखा के समय के बारे में प्रश्न हैं? नीचे हमारे सहायता विशेषज्ञ से पूछें:',
        'k-query-label': '<i class="fa-solid fa-pen"></i> अपना प्रश्न टाइप करें',
        'btn-k-submit': '<i class="fa-solid fa-paper-plane"></i> पूछताछ जमा करें',
        'lbl-k-response-title': 'सहायता विशेषज्ञ प्रतिक्रिया:',
        'placeholder-k-query-input': 'उदा. शाखा का समय क्या है? क्या आप ऋण प्रदान करते हैं?',
        'th-date': 'दिनांक',
        'th-desc': 'विवरण',
        'th-cat': 'श्रेणी',
        'th-type': 'प्रकार',
        'th-amount': 'राशि'
    },
    'mr-IN': {
        'tab-login-btn': 'सुरक्षित लॉगिन',
        'tab-register-btn': 'खाते तयार करा',
        'login-username-label': '<i class="fa-solid fa-user"></i> वापरकर्ता नाव (Username)',
        'login-password-label': '<i class="fa-solid fa-lock"></i> पासवर्ड',
        'login-btn-text': 'खाते ॲक्सेस करा',
        'voice-login-title': 'व्हॉइस पासफ्रेज लॉगिन',
        'voice-login-hint': 'वापरकर्ता नाव टाका आणि पासफ्रेज बोलण्यासाठी माइक दाबा',
        'voice-username-label': '<i class="fa-solid fa-user-tag"></i> वापरकर्ता नाव (पर्यायी)',
        'register-name-label': '<i class="fa-solid fa-signature"></i> पूर्ण नाव',
        'register-username-label': '<i class="fa-solid fa-circle-user"></i> वापरकर्ता नाव निवडा',
        'register-password-label': '<i class="fa-solid fa-key"></i> पासवर्ड निवडा',
        'register-mpin-label': '<i class="fa-solid fa-shield-halved"></i> एमपीआयएन सेट करा (४ अंक)',
        'register-passphrase-label': '<i class="fa-solid fa-microphone-lines"></i> व्हॉइस पासफ्रेज',
        'register-question-label': '<i class="fa-solid fa-circle-question"></i> सुरक्षा प्रश्न',
        'register-answer-label': '<i class="fa-solid fa-pen"></i> सुरक्षा उत्तर',
        'register-btn-text': 'खाते नोंदणी करा',
        'dashboard-balances-title': 'खाते शिल्लक (Balances)',
        'dashboard-savings-label': 'बचत खाते (Savings)',
        'dashboard-checking-label': 'चालू खाते (Current)',
        'dashboard-fd-title': 'अलीकडील मुदत ठेव (FD)',
        'dashboard-fd-principal-label': 'मुद्दल रक्कम',
        'dashboard-fd-tenure-label': 'कालावधी (Tenure)',
        'dashboard-fd-rate-label': 'व्याज दर',
        'dashboard-fd-maturity-label': 'मदत संपण्याची तारीख',
        'dashboard-fd-status-label': 'स्थिती (Status)',
        'dashboard-transfer-title': 'त्वरित पैसे हस्तांतरण',
        'dashboard-transfer-recipient': '<i class="fa-solid fa-user"></i> प्राप्तकर्ता',
        'dashboard-transfer-source': '<i class="fa-solid fa-wallet"></i> माध्यमातून द्या',
        'dashboard-transfer-amount': '<i class="fa-solid fa-indian-rupee-sign"></i> रक्कम (Amount)',
        'dashboard-transfer-mpin': '<i class="fa-solid fa-lock"></i> ४-अंकी एमपीआयएन',
        'dashboard-history-title': 'अलीकडील व्यवहार',
        'dashboard-transfer-btn-text': '<i class="fa-solid fa-paper-plane"></i> पेमेंट पाठवा',
        'mic-hint-ready': 'बैंकिंग कमांड बोलण्यासाठी मायक्रोफोन दाबा',
        'mic-hint-listening': 'ऐकत आहे... आता बोला.',
        'placeholder-login-username': 'वापरकर्ता नाव प्रविष्ट करा (उदा. alice)',
        'placeholder-login-password': 'पासवर्ड प्रविष्ट करा (उदा. password123)',
        'placeholder-voice-login-username': 'वापरकर्ता नाव प्रविष्ट करा (उदा. alice)',
        'placeholder-register-name': 'पूर्ण नाव प्रविष्ट करा',
        'placeholder-register-username': 'एक अद्वितीय वापरकर्ता नाव निवडा',
        'placeholder-register-password': 'पासवर्ड निवडा',
        'placeholder-register-mpin': '4-अंकी पिन प्रविष्ट करा',
        'placeholder-register-passphrase': 'उदा. open sesame',
        'placeholder-register-answer': 'तुमचे उत्तर प्रविष्ट करा',
        'placeholder-reset-username': 'वापरकर्ता नाव प्रविष्ट करा (उदा. alice)',
        'placeholder-reset-answer': 'तुमचे उत्तर प्रविष्ट करा',
        'placeholder-reset-new-password': 'नवीन पासवर्ड प्रविष्ट करा',
        'placeholder-reset-voice-answer': 'तुमचे उत्तर प्रविष्ट करा',
        'placeholder-reset-voice-passphrase': 'पासफ्रेज टाइप करा किंवा बोलण्यासाठी माइक दाबा',
        'option-select-recipient': 'प्राप्तकर्ता निवडा',
        'option-savings': 'बचत खाते (Savings)',
        'option-checking': 'चालू खाते (Current)',
        'option-select-question': 'सुरक्षा प्रश्न निवडा',
        'tab-dashboard': 'डॅशबोर्ड',
        'tab-analytics': 'विश्लेषण आणि अंतर्दृष्टी',
        'filter-duration': 'कालावधी',
        'filter-category': 'वर्ग',
        'filter-type': 'व्यवहार प्रकार',
        'metric-income': 'एकूण उत्पन्न',
        'metric-expense': 'एकूण खर्च',
        'metric-savings': 'निव्वळ बचत',
        'metric-count': 'व्यवहार',
        'chart-spending-trend': 'वेळेनुसार खर्चाचा ट्रेंड',
        'chart-spending-category': 'श्रेणीनुसार खर्च',
        'chart-income-vs-expense': 'उत्पन्न विरुद्ध खर्च तुलना',
        'tab-voice': 'व्हॉइस व्यवहार',
        'tab-knowledge': 'ज्ञान केंद्र',
        'voice-mic-header': 'व्हॉइस नियंत्रण',
        'voice-transactions-title': 'व्हॉइस व्यवहार लेजर',
        'k-card-title1': 'व्यवहार सुरक्षा',
        'k-card-desc1': 'सर्व पेमेंटसाठी तुमच्या युनिक ४-अंकी एमपीआयएनची आवश्यकता असते. तुमचा एमपीआयएन किंवा पासवर्ड कधीही कोणाशीही शेअर करू नका. सुरक्षेचा स्तर जोडण्यासाठी, तुमची युनिक व्हॉइस बायोमेट्रिक प्रिंट नोंदवा।',
        'k-card-title2': 'मर्यादा आणि नियम',
        'k-card-desc2': 'बचत खात्यात दररोज व्हॉइस ट्रान्सफरची मर्यादा ₹५०,००० आहे. लॉक-इन कालावधीनुसार मुदत ठेवीचे व्याजदर ६.५% ते ७.८% पर्यंत असतात।',
        'k-card-title3': 'व्हॉइस कमांड मार्गदर्शक',
        'k-card-desc3': 'निधीवाणी एआय नैसर्गिक बोलल्या जाणाऱ्या कमांड समजण्यासाठी प्रगत लॅन्ग्राफ राउटिंगचा वापर करते. इंग्रजी, हिंदी किंवा मराठीत थेट बोलण्याचा प्रयत्न करा।',
        'k-prompts-title': 'उदाहरण व्हॉइस प्रॉम्प्ट्स',
        'k-prompts-intro': 'व्हॉइस असिस्टंट पॅनेलमध्ये ते वापरून पाहण्यासाठी खालील कोणत्याही उदाहरण कमांडवर क्लिक करा:',
        'k-cat-account': 'खाते आणि शिल्लक',
        'k-cat-transfer': 'पैसे हस्तांतरण',
        'k-cat-fd': 'मुदत ठेवी',
        'k-cat-multilingual': 'बहुभाषिक उदाहरणे',
        'btn-k-prompt-sbal': '"माझ्या बचत खात्यातील शिल्लक तपासा"',
        'btn-k-prompt-ledger': '"माझे अलीकडील व्यवहार दाखवा"',
        'btn-k-prompt-cbal': '"माझ्या चालू खात्यातील शिल्लक तपासा"',
        'btn-k-prompt-send-alice': '"बचत खात्यातून एलिस स्मिथला ₹२०० पाठवा"',
        'btn-k-prompt-send-bob': '"चालू खात्यातून बॉब जोन्सला ₹१५०० ट्रान्सफर करा"',
        'btn-k-prompt-fd-details': '"माझे फिक्स डिपॉझिट तपशील दाखवा"',
        'btn-k-prompt-fd-rates': '"नवीनतम एफडी व्याज दर काय आहे?"',
        'k-support-title': 'सहायता डेस्क',
        'k-support-intro': 'व्याजदर, बँकिंग धोरणे किंवा शाखेच्या वेळेबद्दल काही प्रश्न आहेत? खालील आमच्या मदत तज्ञाला विचारा:',
        'k-query-label': '<i class="fa-solid fa-pen"></i> तुमचा प्रश्न टाइप करा',
        'btn-k-submit': '<i class="fa-solid fa-paper-plane"></i> चौकशी सबमिट करा',
        'lbl-k-response-title': 'मदत तज्ञाचा प्रतिसाद:',
        'placeholder-k-query-input': 'उदा. शाखेची वेळ काय आहे? तुम्ही कर्ज देता का?',
        'th-date': 'तारीख',
        'th-desc': 'तपशील',
        'th-cat': 'वर्ग',
        'th-type': 'प्रकार',
        'th-amount': 'रक्कम'
    }
};

function translateUI() {
    const lang = selectedLanguage;
    const langData = translations[lang] || translations['en-IN'];

    for (const selector in elementSelectors) {
        const key = elementSelectors[selector];
        const el = document.querySelector(selector);
        if (el && langData[key]) {
            el.innerHTML = langData[key];
        }
    }

    for (const selector in placeholderSelectors) {
        const key = placeholderSelectors[selector];
        const el = document.querySelector(selector);
        if (el && langData[key]) {
            el.placeholder = langData[key];
        }
    }

    if (micHintText) {
        if (isRecording) {
            micHintText.textContent = langData['mic-hint-listening'];
        } else {
            micHintText.textContent = langData['mic-hint-ready'];
        }
    }
}

// Audio Recording State
let mediaRecorder = null;
let audioChunks = [];
let voiceAudioBase64 = null;
let voiceAudioMime = null;
let enrolledVoiceAudioBase64 = null;
let enrolledVoiceAudioMime = null;
let resetVoiceAudioBase64 = null;
let resetVoiceAudioMime = null;

async function startAudioRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        let mimeType = 'audio/webm';
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
            mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
            mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
            mimeType = 'audio/ogg;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
            mimeType = 'audio/mp4';
        }

        voiceAudioMime = mimeType;
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType });

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.start();
        console.log("MediaRecorder started with MIME:", mimeType);
    } catch (err) {
        console.error("Error starting audio recording:", err);
    }
}

function stopAudioRecording() {
    return new Promise((resolve) => {
        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            resolve(null);
            return;
        }

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: voiceAudioMime });
            if (mediaRecorder.stream) {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }

            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = () => {
                const base64Data = reader.result.split(',')[1];
                resolve(base64Data);
            };
        };

        mediaRecorder.stop();
    });
}

// Speech Recognition & Synthesis Initialization
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = selectedLanguage;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        if (activeSpeechMode === 'assistant') {
            isRecording = true;
            micContainer.classList.add('recording');
            micIcon.className = 'fa-solid fa-square';
            micHintText.textContent = "Listening... Speak now.";
            const activeIndicator = document.querySelector('.voice-active-indicator');
            if (activeIndicator) activeIndicator.classList.add('listening');
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
        } else if (activeSpeechMode === 'voice2fa') {
            voice2FAStatus.className = 'voice-2fa-status error';
            voice2FAStatus.textContent = `Error: ${event.error}`;
        } else if (activeSpeechMode === 'dictate_reset_voice') {
            const badge = document.getElementById('reset-voice-enrollment-badge');
            if (badge) {
                badge.className = 'voice-enrollment-badge error';
                badge.textContent = `Error: ${event.error}`;
            }
        }
    };

    recognition.onend = () => {
        stopSpeechEngine();
    };

    recognition.onresult = async (event) => {
        const transcript = event.results[0][0].transcript;
        if (activeSpeechMode === 'assistant') {
            handleUserSpeech(transcript);
        } else if (activeSpeechMode === 'login') {
            voiceLoginStatus.textContent = "Processing voice print...";
            const base64Audio = await stopAudioRecording();
            handleVoiceLogin(transcript, base64Audio);
        } else if (activeSpeechMode === 'dictate') {
            const base64Audio = await stopAudioRecording();
            handleDictatePassphrase(transcript, base64Audio);
        } else if (activeSpeechMode === 'voice2fa') {
            voice2FAStatus.textContent = "Processing voice print...";
            const base64Audio = await stopAudioRecording();
            handleVoice2FA(transcript, base64Audio);
        } else if (activeSpeechMode === 'dictate_reset_voice') {
            const base64Audio = await stopAudioRecording();
            handleResetVoiceDictate(transcript, base64Audio);
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
    const dictateResetVoiceBtn = document.getElementById('dictate-reset-voice-btn');
    if (dictateResetVoiceBtn) {
        dictateResetVoiceBtn.disabled = true;
        dictateResetVoiceBtn.style.opacity = '0.5';
    }
}

function stopSpeechEngine() {
    isRecording = false;
    micContainer.classList.remove('recording');
    micIcon.className = 'fa-solid fa-microphone';
    micHintText.textContent = "Tap the microphone to speak a banking command";
    const activeIndicator = document.querySelector('.voice-active-indicator');
    if (activeIndicator) activeIndicator.classList.remove('listening');

    isVoiceLoginRecording = false;
    voiceLoginMicWrapper.classList.remove('listening');
    if (activeSpeechMode === 'login' && voiceLoginStatus.textContent === "Listening to passphrase...") {
        voiceLoginStatus.textContent = "Tap mic to retry";
    }

    isDictateRecording = false;
    dictatePassphraseBtn.classList.remove('listening');

    isResetVoiceRecording = false;
    const dictateResetVoiceBtn = document.getElementById('dictate-reset-voice-btn');
    if (dictateResetVoiceBtn) {
        dictateResetVoiceBtn.classList.remove('listening');
    }

    isVoice2FARecording = false;
    if (typeof voice2FAMicBtn !== 'undefined' && voice2FAMicBtn) {
        voice2FAMicBtn.parentElement.classList.remove('listening');
        const icon = document.getElementById('voice-2fa-mic-icon');
        if (icon) icon.className = 'fa-solid fa-microphone';
    }
    if (activeSpeechMode === 'voice2fa' && typeof voice2FAStatus !== 'undefined' && voice2FAStatus.textContent === "Listening to passphrase...") {
        voice2FAStatus.textContent = "Tap mic to retry";
    }

    // Stop MediaRecorder if running and discard
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try {
            mediaRecorder.stop();
            if (mediaRecorder.stream) {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        } catch (e) {
            console.error("Error stopping mediaRecorder during shutdown:", e);
        }
    }
}

// Speak response out loud using browser TTS
function speakText(text) {
    if (!('speechSynthesis' in window)) return;

    let textToSpeak = text;
    // If the response contains a table, filter out the rows so they are not spoken out
    if (text.includes('|')) {
        const lines = text.split('\n');
        const nonTableLines = lines.filter(line => !line.trim().startsWith('|'));
        textToSpeak = nonTableLines.join(' ').trim();
        if (!textToSpeak) {
            textToSpeak = "Here is your transaction history.";
        }
    }

    const cleanText = textToSpeak.replace(/\[Simulation Mode\]/g, '').replace(/\[Simulation\]/g, '').trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    let targetVoice = null;
    utterance.lang = selectedLanguage;

    if (selectedLanguage === 'hi-IN') {
        targetVoice = voices.find(voice =>
            voice.lang.includes('hi') || voice.name.includes('हिन्दी') || voice.name.includes('Hindi')
        );
    } else if (selectedLanguage === 'mr-IN') {
        targetVoice = voices.find(voice =>
            voice.lang.includes('mr') || voice.name.includes('मराठी') || voice.name.includes('Marathi')
        );
        if (!targetVoice) {
            targetVoice = voices.find(voice =>
                voice.lang.includes('hi') || voice.name.includes('हिन्दी') || voice.name.includes('Hindi')
            );
        }
    } else {
        targetVoice = voices.find(voice =>
            voice.lang.includes('en') && (voice.name.includes('Google') || voice.name.includes('Natural') || voice.name.includes('Samantha'))
        );
    }
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
    const mpin = document.getElementById('register-mpin').value;
    const voicePassphrase = document.getElementById('register-passphrase').value;
    const securityQuestion = document.getElementById('register-question').value;
    const securityAnswer = document.getElementById('register-answer').value;

    // Enrolling voice audio print is now optional, so we bypass this validation.

    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                username,
                password,
                mpin,
                voice_passphrase: voicePassphrase,
                voice_audio_base64: enrolledVoiceAudioBase64,
                voice_audio_mime: enrolledVoiceAudioMime,
                security_question: securityQuestion,
                security_answer: securityAnswer,
                face_image_base64: capturedFaceBase64
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
            enrolledVoiceAudioBase64 = null;
            enrolledVoiceAudioMime = null;
            capturedFaceBase64 = null;
            const badge = document.getElementById('voice-enrollment-badge');
            if (badge) {
                badge.className = 'voice-enrollment-badge';
                badge.textContent = '';
            }
            const faceBadge = document.getElementById('face-register-status');
            if (faceBadge) {
                faceBadge.className = 'face-enrollment-badge';
                faceBadge.textContent = 'No face scanned yet';
            }

            loginUser(data.username, data.name);
        }
    } catch (err) {
        console.error(err);
        alert("Registration server error.");
    }
});
logoutBtn.addEventListener('click', () => {
    logoutUser();
});

// Trigger login context UI
function loginUser(username, name) {
    currentUser = { username, name };
    sessionStorage.setItem('currentUser', JSON.stringify(currentUser));

    // Toggle container views
    authContainer.classList.add('hidden');
    dashboardContainer.classList.remove('hidden');
    userProfile.classList.remove('hidden');
    loggedUserName.textContent = name;

    // Switch to Summary Tab as default after login
    if (typeof switchDashboardTab === 'function') {
        switchDashboardTab('tab-summary-btn');
    }

    // Load initial user state
    fetchInitialState(username);

    // Populate Quick Transfer recipients
    populatePaymentRecipients(username);

    // Speak welcome message
    speakText(`Welcome to NidhiVani AI, ${name}! How can I help you today?`);
}

function logoutUser() {
    window.speechSynthesis.cancel();
    sessionStorage.removeItem('currentUser');
    currentUser = null;
    window.location.reload();
}

// Speech Actions orchestration

// 1. Voice login mic trigger
voiceLoginBtn.addEventListener('click', async () => {
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

        await startAudioRecording();
        recognition.lang = selectedLanguage;
        recognition.start();
    }
});

// Handle matched voice login transcription
async function handleVoiceLogin(text, base64Audio) {
    if (!text || text.trim() === '') {
        voiceLoginStatus.textContent = "No voice heard. Try again.";
        return;
    }
    voiceLoginStatus.className = 'voice-login-status processing';
    voiceLoginStatus.textContent = `Verifying passphrase...`;

    const voiceUsername = document.getElementById('voice-login-username').value.trim();

    try {
        const response = await fetch('/api/voice-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: voiceUsername || null,
                passphrase: text,
                voice_audio_base64: base64Audio,
                voice_audio_mime: voiceAudioMime
            })
        });

        const data = await response.json();
        if (data.success) {
            voiceLoginStatus.className = 'voice-login-status success';
            voiceLoginStatus.textContent = data.message || "Welcome back!";
            speakText(`Voice verification successful. Welcome back, ${data.name}!`);
            setTimeout(() => {
                loginUser(data.username, data.name);
            }, 1500);
        } else {
            voiceLoginStatus.className = 'voice-login-status error';
            voiceLoginStatus.textContent = data.message || "Voice print not matched.";
            speakText(data.message || "Access denied. Voice print not recognized.");
        }
    } catch (err) {
        console.error(err);
        voiceLoginStatus.className = 'voice-login-status error';
        voiceLoginStatus.textContent = "Auth server offline.";
        speakText("Biometric verification server offline.");
    }
}

// 2. Dictate voice passphrase in Registration
dictatePassphraseBtn.addEventListener('click', async () => {
    if (!recognition) return;
    if (isDictateRecording) {
        recognition.stop();
    } else {
        window.speechSynthesis.cancel();
        activeSpeechMode = 'dictate';
        isDictateRecording = true;
        dictatePassphraseBtn.classList.add('listening');

        await startAudioRecording();
        recognition.lang = selectedLanguage;
        recognition.start();
    }
});

function handleDictatePassphrase(text, base64Audio) {
    if (!text || text.trim() === '') return;
    const phrase = text.replace(/[.!?]/g, '').trim().toLowerCase();
    document.getElementById('register-passphrase').value = phrase;

    enrolledVoiceAudioBase64 = base64Audio;
    enrolledVoiceAudioMime = voiceAudioMime;

    const badge = document.getElementById('voice-enrollment-badge');
    if (badge) {
        badge.className = 'voice-enrollment-badge success';
        badge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Voice print captured successfully!';
    }

    speakText(`Recorded passphrase and captured voice print successfully.`);
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
            recognition.lang = selectedLanguage;
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

// MPIN typing entry confirm & cancel buttons click actions
mpinSubmitBtn.addEventListener('click', () => {
    const pin = typeMpinInput.value.trim();
    if (pin.length === 4) {
        handleUserSpeech(pin);
        typeMpinInput.value = '';
    } else {
        alert("Please enter a valid 4-digit MPIN.");
    }
});

mpinCancelBtn.addEventListener('click', () => {
    handleUserSpeech("cancel");
    typeMpinInput.value = '';
});

typeMpinInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        mpinSubmitBtn.click();
    }
});

// PDF Statement Modal triggers and form handling
if (statementModalBtn) {
    statementModalBtn.addEventListener('click', () => {
        statementModal.classList.remove('hidden');
        statementForm.reset();
        dateRangeInputs.classList.add('hidden');
        statementStartDate.value = '';
        statementEndDate.value = '';
    });
}

const hideStatementModal = () => {
    statementModal.classList.add('hidden');
};

if (closeStatementModalBtn) closeStatementModalBtn.addEventListener('click', hideStatementModal);
if (cancelStatementBtn) cancelStatementBtn.addEventListener('click', hideStatementModal);

statementModal.addEventListener('click', (e) => {
    if (e.target === statementModal) {
        hideStatementModal();
    }
});

document.querySelectorAll('input[name="statement-scope"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        if (e.target.value === 'datewise') {
            dateRangeInputs.classList.remove('hidden');
        } else {
            dateRangeInputs.classList.add('hidden');
        }
    });
});

statementForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser) return;

    const scope = document.querySelector('input[name="statement-scope"]:checked').value;
    let limit = null;
    let startDate = null;
    let endDate = null;

    if (scope === 'datewise') {
        startDate = statementStartDate.value;
        endDate = statementEndDate.value;
        if (!startDate || !endDate) {
            alert("Please select both start and end dates.");
            return;
        }
    } else {
        limit = parseInt(scope);
    }

    const generateBtn = document.getElementById('generate-pdf-btn');
    const originalHtml = generateBtn.innerHTML;
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

    try {
        let url = `/api/transactions?username=${encodeURIComponent(currentUser.username)}`;
        if (limit) url += `&limit=${limit}`;
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;

        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch transactions`);
        }

        const transactions = await response.json();
        if (transactions.length === 0) {
            alert("No transactions found matching the selected filters.");
        } else {
            await generatePDFStatement(transactions, scope, startDate, endDate);
        }
        hideStatementModal();
    } catch (err) {
        console.error(err);
        alert("Error generating PDF statement. Please try again.");
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = originalHtml;
    }
});

// Generate and save banking transaction statement PDF
async function generatePDFStatement(transactions, scope, startDate, endDate) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const primaryColor = [20, 28, 47]; // #141c2f (Dark Navy)

    // Add Header Bar
    doc.setFillColor(...primaryColor);
    doc.rect(0, 0, 210, 40, 'F');

    // Branding Title
    doc.setFont("Helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(255, 255, 255);
    doc.text("NIDHIVANI AI", 15, 24);

    // Subtitle
    doc.setFont("Helvetica", "normal");
    doc.setFontSize(9.5);
    doc.setTextColor(144, 160, 199);
    doc.text("Secure Digital Voice Banking Statement", 15, 31);

    // Customer details (Right-aligned in header)
    doc.setFont("Helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(255, 255, 255);
    doc.text(`Account Holder: ${currentUser.name}`, 195, 17, { align: "right" });
    doc.text(`Username: ${currentUser.username}`, 195, 23, { align: "right" });
    doc.text(`Generated: ${new Date().toLocaleString()}`, 195, 29, { align: "right" });

    // Main Document Header
    doc.setFont("Helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(...primaryColor);
    doc.text("ACCOUNT TRANSACTION STATEMENT", 15, 54);

    doc.setFont("Helvetica", "normal");
    doc.setFontSize(9.5);
    doc.setTextColor(100, 100, 100);
    let filterText = `Scope: Last ${transactions.length} transactions`;
    if (scope === 'datewise') {
        filterText = `Filter: Date Range from ${startDate} to ${endDate}`;
    }
    doc.text(filterText, 15, 60);

    // Table Columns & Rows
    const columns = [
        { header: 'ID', dataKey: 'id' },
        { header: 'Date', dataKey: 'date' },
        { header: 'Description', dataKey: 'description' },
        { header: 'Category', dataKey: 'category' },
        { header: 'Type', dataKey: 'type' },
        { header: 'Amount', dataKey: 'amount' }
    ];

    const rows = transactions.map((tx) => {
        const sign = tx.type.toLowerCase() === 'credit' ? '+' : '-';
        return {
            id: `TX-${String(tx.id).padStart(5, '0')}`,
            date: tx.date,
            description: tx.description,
            category: tx.category,
            type: tx.type,
            amount: `${sign} Rs. ${tx.amount.toFixed(2)}`
        };
    });

    // Render AutoTable PDF layout
    doc.autoTable({
        columns: columns,
        body: rows,
        startY: 66,
        theme: 'striped',
        headStyles: {
            fillColor: primaryColor,
            textColor: [255, 255, 255],
            fontStyle: 'bold',
            halign: 'left'
        },
        bodyStyles: {
            fontSize: 8.5,
            textColor: [50, 50, 50]
        },
        columnStyles: {
            id: { cellWidth: 20 },
            date: { cellWidth: 32 },
            description: { cellWidth: 48 },
            category: { cellWidth: 32 },
            type: { cellWidth: 22 },
            amount: { cellWidth: 26, fontStyle: 'bold', halign: 'right' }
        },
        alternateRowStyles: {
            fillColor: [245, 247, 250]
        },
        didParseCell: function (data) {
            if (data.column.key === 'amount' && data.cell.section === 'body') {
                const textVal = data.cell.text[0];
                if (textVal.startsWith('+')) {
                    data.cell.styles.textColor = [0, 180, 80]; // Green
                } else if (textVal.startsWith('-')) {
                    data.cell.styles.textColor = [220, 50, 50]; // Red
                }
            }
        }
    });

    // Submit PDF data to backend to trigger native browser file download (bypasses Blob URL UUID download issues)
    const pdfBase64 = doc.output('datauristring').split(',')[1];
    document.getElementById('pdf-form-data').value = pdfBase64;
    document.getElementById('pdf-form-filename').value = `NidhiVani_Statement_${currentUser.username}_${Date.now()}.pdf`;
    document.getElementById('pdf-download-form').submit();
}

// Communicate voice speech inputs to the chat server
async function handleUserSpeech(text) {
    if (!text || text.trim() === '' || !currentUser) return;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Create and append User Chat Bubble
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user-bubble';

    const userTag = document.createElement('span');
    userTag.className = 'bubble-tag';
    userTag.textContent = 'You:';

    const userText = document.createElement('p');
    userText.textContent = text;

    userBubble.appendChild(userTag);
    userBubble.appendChild(userText);

    // Add WhatsApp metadata row for user
    const userMeta = document.createElement('div');
    userMeta.className = 'whatsapp-meta-row';
    userMeta.innerHTML = `<span>${timeStr}</span><i class="fa-solid fa-check-double" style="color: #34b7f1; margin-left: 2px;"></i>`;
    userBubble.appendChild(userMeta);

    chatDisplay.appendChild(userBubble);

    // Create and append Assistant Chat Bubble (with loading status)
    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'chat-bubble assistant-bubble';

    const assistantTag = document.createElement('span');
    assistantTag.className = 'bubble-tag';
    assistantTag.textContent = 'NidhiVani Assistant:';

    const assistantText = document.createElement('p');
    assistantText.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Checking ledger...';

    assistantBubble.appendChild(assistantTag);
    assistantBubble.appendChild(assistantText);

    // Add WhatsApp metadata row for assistant
    const assistantMeta = document.createElement('div');
    assistantMeta.className = 'whatsapp-meta-row';
    assistantMeta.innerHTML = `<span>${timeStr}</span>`;
    assistantBubble.appendChild(assistantMeta);

    chatDisplay.appendChild(assistantBubble);

    const scrollChatToBottom = () => {
        if (chatDisplay) chatDisplay.scrollTop = chatDisplay.scrollHeight;
    };
    scrollChatToBottom();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                username: currentUser.username,
                language: selectedLanguage
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update assistant tag to show active agent name
        if (data.active_agent) {
            assistantTag.textContent = `NidhiVani [${data.active_agent}]:`;
        } else {
            assistantTag.textContent = 'NidhiVani Assistant:';
        }

        // Render speech result in the specific bubble
        assistantText.innerHTML = formatAssistantResponse(data.response);
        scrollChatToBottom();
        updateDashboard(data.state);
        if (data.queried_transactions) {
            updateTransactionsTable(data.queried_transactions);
        }
        speakText(data.response);

        // Toggle MPIN input entry wrapper based on pending transaction state
        if (data.pending_transfer) {
            mpinInputWrapper.classList.remove('hidden');
            typeMpinInput.value = '';
            typeMpinInput.focus();
            scrollChatToBottom();
        } else {
            mpinInputWrapper.classList.add('hidden');
            typeMpinInput.value = '';
        }

        // Handle forced logout if too many incorrect MPIN attempts
        if (data.logout) {
            // Stop speech recognition and recording status
            stopSpeechEngine();
            if (recognition) {
                try {
                    recognition.abort();
                } catch (e) {
                    console.error("Error aborting speech recognition:", e);
                }
            }

            // Disable UI inputs so user cannot perform actions
            if (micBtn) micBtn.disabled = true;
            if (mpinSubmitBtn) mpinSubmitBtn.disabled = true;
            if (mpinCancelBtn) mpinCancelBtn.disabled = true;
            if (typeMpinInput) typeMpinInput.disabled = true;

            // Show a visual countdown inside the response bubble
            let secondsLeft = 5;
            const logoutMsgId = `logout-countdown-msg-${Date.now()}`;
            const logoutInterval = setInterval(() => {
                secondsLeft--;
                const countdownEl = document.getElementById(logoutMsgId);
                if (countdownEl) {
                    countdownEl.innerHTML = `<i class="fa-solid fa-arrow-right-from-bracket"></i> Logging out in ${secondsLeft} seconds...`;
                }
                scrollChatToBottom();
                if (secondsLeft <= 0) {
                    clearInterval(logoutInterval);
                    logoutUser();
                }
            }, 1000);

            // Initial visual indicator
            assistantText.innerHTML += `<div id="${logoutMsgId}" style="color: #ff4a4a; font-weight: bold; margin-top: 12px; font-size: 0.95rem; animation: textPulse 1.2s infinite ease-in-out;"><i class="fa-solid fa-arrow-right-from-bracket"></i> Logging out in ${secondsLeft} seconds...</div>`;
            scrollChatToBottom();
        }

    } catch (error) {
        console.error('API Error:', error);
        assistantText.textContent = "Error communicating with NidhiVani AI ledger service.";
        scrollChatToBottom();
        speakText("I encountered an error communicating with the banking server.");
    }
}

// Update the visual dashboard cards
function updateDashboard(state) {
    if (!state) return;

    updateValueWithAnimation(savingsBalanceEl, `₹${state.balances.savings.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);
    updateValueWithAnimation(checkingBalanceEl, `₹${state.balances.checking.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`);

    if (state.fixed_deposits && state.fixed_deposits.length > 0) {
        const fd = state.fixed_deposits[0];
        updateValueWithAnimation(fdAmountEl, `₹${fd.principal_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`);
        updateValueWithAnimation(fdTenureEl, fd.tenure);
        updateValueWithAnimation(fdRateEl, fd.interest_rate);
        updateValueWithAnimation(fdMaturityEl, fd.maturity_date);
        updateValueWithAnimation(fdStatusEl, fd.status);
        document.getElementById('fd-container').style.display = 'block';
    } else {
        // If user doesn't have an FD, hide/clear card metrics
        fdAmountEl.textContent = "₹0.00";
        fdTenureEl.textContent = "-";
        fdRateEl.textContent = "-";
        fdMaturityEl.textContent = "-";
        fdStatusEl.textContent = "-";
    }

    if (state.transactions) {
        updateTransactionsTable(state.transactions);
    }
}

let activeTransactions = [];

function updateTransactionsTable(transactions) {
    activeTransactions = transactions || [];
    // Reset search input value when new transactions are loaded
    const txSearchInput = document.getElementById('tx-search-input');
    if (txSearchInput) {
        txSearchInput.value = '';
    }
    renderFilteredTransactions(activeTransactions);
    renderAnalytics();
}

function renderFilteredTransactions(transactions) {
    const bodies = [transactionsBody, document.getElementById('voice-transactions-body')];

    bodies.forEach(body => {
        if (!body) return;
        body.innerHTML = '';

        if (transactions.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `<td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 2rem;">No matching transactions found</td>`;
            body.appendChild(emptyRow);
            return;
        }

        transactions.forEach(tx => {
            const row = document.createElement('tr');
            const amountClass = tx.type.toLowerCase() === 'credit' ? 'credit' : 'debit';
            const sign = tx.type.toLowerCase() === 'credit' ? '+' : '-';

            row.innerHTML = `
                <td>${tx.date}</td>
                <td><strong>${tx.description}</strong></td>
                <td>${tx.category}</td>
                <td><span class="tx-type-badge ${amountClass}">${tx.type}</span></td>
                <td class="text-right tx-amount ${amountClass}">${sign}₹${tx.amount.toFixed(2)}</td>
            `;
            body.appendChild(row);
        });
    });
}

function updateValueWithAnimation(element, newValue) {
    const isBalance = element.id === 'savings-balance' || element.id === 'checking-balance' || element.id === 'fd-amount';

    if (isBalance) {
        element.dataset.realValue = newValue;
        const isVisible = balancesVisible[element.id];
        const displayValue = isVisible ? newValue : '₹ ••••••';

        if (element.textContent !== displayValue) {
            element.textContent = displayValue;
            const cardParent = element.closest('.card');
            if (cardParent) {
                cardParent.classList.remove('flash-update');
                void cardParent.offsetWidth;
                cardParent.classList.add('flash-update');
            }
        }
    } else {
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
    // Bind toggle balance visibility buttons
    document.querySelectorAll('.toggle-balance-visibility').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = btn.dataset.target;
            const targetEl = document.getElementById(targetId);
            if (!targetEl) return;

            balancesVisible[targetId] = !balancesVisible[targetId];

            if (balancesVisible[targetId]) {
                // Currently visible, show actual value and set eye icon
                targetEl.textContent = targetEl.dataset.realValue || '₹0.00';
                btn.classList.remove('fa-eye-slash');
                btn.classList.add('fa-eye');
            } else {
                // Currently hidden, mask value and set eye-slash icon
                targetEl.textContent = '₹ ••••••';
                btn.classList.remove('fa-eye');
                btn.classList.add('fa-eye-slash');
            }
        });
    });

    // Bind user profile icon click to show full name tooltip
    const profileIcon = document.getElementById('user-profile-icon');
    const nameTooltip = document.getElementById('full-name-tooltip');
    if (profileIcon && nameTooltip) {
        profileIcon.addEventListener('click', (e) => {
            e.stopPropagation();
            if (nameTooltip.classList.contains('hidden')) {
                nameTooltip.textContent = currentUser ? currentUser.name : 'User Profile';
                nameTooltip.classList.remove('hidden');
            } else {
                nameTooltip.classList.add('hidden');
            }
        });

        // Hide tooltip if clicked anywhere else
        document.addEventListener('click', () => {
            nameTooltip.classList.add('hidden');
        });
    }

    const appLanguageSelector = document.getElementById('app-language-selector');
    if (appLanguageSelector) {
        appLanguageSelector.value = selectedLanguage;
        appLanguageSelector.addEventListener('change', (e) => {
            selectedLanguage = e.target.value;
            localStorage.setItem('appLanguage', selectedLanguage);
            translateUI();

            if (selectedLanguage === 'hi-IN') {
                speakText("भाषा बदलकर हिंदी कर दी गई है।");
            } else if (selectedLanguage === 'mr-IN') {
                speakText("भाषा बदलून मराठी करण्यात आली आहे.");
            } else {
                speakText("Language changed to English.");
            }
        });
    }
    translateUI();

    // Bind transaction search inputs listener
    const txSearchInput = document.getElementById('tx-search-input');
    const voiceTxSearchInput = document.getElementById('voice-tx-search-input');

    const handleSearchInput = (e) => {
        const query = e.target.value.toLowerCase().trim();

        // Sync values across inputs
        if (txSearchInput && e.target === voiceTxSearchInput) txSearchInput.value = e.target.value;
        if (voiceTxSearchInput && e.target === txSearchInput) voiceTxSearchInput.value = e.target.value;

        if (!query) {
            renderFilteredTransactions(activeTransactions);
            return;
        }
        const filtered = activeTransactions.filter(tx => {
            return (
                (tx.date && tx.date.toLowerCase().includes(query)) ||
                (tx.description && tx.description.toLowerCase().includes(query)) ||
                (tx.category && tx.category.toLowerCase().includes(query)) ||
                (tx.type && tx.type.toLowerCase().includes(query)) ||
                (tx.amount && tx.amount.toString().includes(query))
            );
        });
        renderFilteredTransactions(filtered);
    };

    if (txSearchInput) {
        txSearchInput.addEventListener('input', handleSearchInput);
    }
    if (voiceTxSearchInput) {
        voiceTxSearchInput.addEventListener('input', handleSearchInput);
    }

    const session = sessionStorage.getItem('currentUser');
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

// Helper to format assistant responses, converting markdown tables to styled HTML tables
function formatAssistantResponse(text) {
    if (!text) return "";

    // Check if the text contains a markdown table structure
    if (text.includes('|') && text.includes('\n|')) {
        const lines = text.split('\n');
        let inTable = false;
        let htmlResult = [];
        let tableHtml = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            if (line.startsWith('|') && line.endsWith('|')) {
                if (!inTable) {
                    inTable = true;
                    tableHtml.push('<div class="chat-table-wrapper"><table class="chat-tx-table">');
                }

                // Skip separator rows like |:---|---|
                if (line.includes('---')) continue;

                const cells = line.split('|').slice(1, -1).map(c => c.trim().replace(/\*\*/g, ''));
                tableHtml.push('<tr>');
                cells.forEach(cell => {
                    const tag = tableHtml.length === 2 ? 'th' : 'td'; // First row is header

                    // Determine amount highlighting if credit/debit sign
                    let cellClass = "";
                    if (tag === 'td') {
                        if (cell.startsWith('+')) cellClass = 'class="credit"';
                        else if (cell.startsWith('-')) cellClass = 'class="debit"';
                    }

                    tableHtml.push(`<${tag} ${cellClass}>${cell}</${tag}>`);
                });
                tableHtml.push('</tr>');
            } else {
                if (inTable) {
                    inTable = false;
                    tableHtml.push('</table></div>');
                    htmlResult.push(tableHtml.join(''));
                    tableHtml = [];
                }
                // Pre-process inline bold in ordinary text blocks
                let parsedLine = line
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                htmlResult.push(parsedLine ? `<p>${parsedLine}</p>` : '<br>');
            }
        }
        if (inTable) {
            tableHtml.push('</table></div>');
            htmlResult.push(tableHtml.join(''));
        }
        return htmlResult.join('');
    }

    // Fallback: replace newlines with <br> and bold formatting
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

// --- Voice 2FA Verification Flow ---

const voice2FAModal = document.getElementById('voice-2fa-modal');
const closeVoice2FAModalBtn = document.getElementById('close-voice-2fa-modal');
const cancelVoice2FABtn = document.getElementById('cancel-voice-2fa-btn');
const voice2FAMicBtn = document.getElementById('voice-2fa-mic-btn');
const voice2FAStatus = document.getElementById('voice-2fa-status');
const voice2FAPassphrasePrompt = document.getElementById('voice-2fa-passphrase-prompt');

const hideVoice2FAModal = () => {
    voice2FAModal.classList.add('hidden');
    stopSpeechEngine();
    pending2FAUser = null;
};

if (closeVoice2FAModalBtn) closeVoice2FAModalBtn.addEventListener('click', hideVoice2FAModal);
if (cancelVoice2FABtn) cancelVoice2FABtn.addEventListener('click', hideVoice2FAModal);

voice2FAModal.addEventListener('click', (e) => {
    if (e.target === voice2FAModal) {
        hideVoice2FAModal();
    }
});

voice2FAMicBtn.addEventListener('click', async () => {
    if (!recognition) return;
    if (isVoice2FARecording) {
        recognition.stop();
    } else {
        window.speechSynthesis.cancel();
        activeSpeechMode = 'voice2fa';
        isVoice2FARecording = true;
        voice2FAMicBtn.parentElement.classList.add('listening');
        const icon = document.getElementById('voice-2fa-mic-icon');
        if (icon) icon.className = 'fa-solid fa-square';
        voice2FAStatus.className = 'voice-2fa-status';
        voice2FAStatus.textContent = "Listening to passphrase...";

        await startAudioRecording();
        recognition.lang = selectedLanguage;
        recognition.start();
    }
});

async function handleVoice2FA(text, base64Audio) {
    if (!text || text.trim() === '') {
        voice2FAStatus.textContent = "No voice heard. Try again.";
        return;
    }
    voice2FAStatus.className = 'voice-2fa-status processing';
    voice2FAStatus.textContent = `Verifying passphrase...`;

    try {
        const response = await fetch('/api/voice-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: pending2FAUser.username,
                passphrase: text,
                voice_audio_base64: base64Audio,
                voice_audio_mime: voiceAudioMime
            })
        });

        const data = await response.json();
        if (data.success) {
            voice2FAStatus.className = 'voice-2fa-status success';
            voice2FAStatus.textContent = data.message || "Voice verified!";
            speakText(`Voice verification successful. Welcome back, ${data.name}!`);
            setTimeout(() => {
                hideVoice2FAModal();
                loginUser(data.username, data.name);
            }, 1500);
        } else {
            voice2FAStatus.className = 'voice-2fa-status error';
            voice2FAStatus.textContent = data.message || "Voice print mismatch.";
            speakText(data.message || "Access denied. Voice print not recognized.");
        }
    } catch (err) {
        console.error(err);
        voice2FAStatus.className = 'voice-2fa-status error';
        voice2FAStatus.textContent = "Auth server offline.";
        speakText("Biometric verification server offline.");
    }
}

// --- Password Reset & Settings UI Logic ---
const resetPasswordModal = document.getElementById('reset-password-modal');
const closeResetModalBtn = document.getElementById('close-reset-modal');
const cancelResetBtn = document.getElementById('cancel-reset-btn');
const resetPasswordForm = document.getElementById('reset-password-form');
const resetUsernameGroup = document.getElementById('reset-username-group');
const resetUsernameInput = document.getElementById('reset-username');
const resetGetQuestionBtn = document.getElementById('reset-get-question-btn');
const resetQAGroup = document.getElementById('reset-qa-group');
const resetQuestionText = document.getElementById('reset-question-text');
const resetAnswerInput = document.getElementById('reset-answer');
const resetNewPasswordInput = document.getElementById('reset-new-password');
const submitResetBtn = document.getElementById('submit-reset-btn');
const forgotPasswordLink = document.getElementById('forgot-password-link');
const dropdownResetBtn = document.getElementById('dropdown-reset-password-btn');

const showResetModal = (isLoggedIn = false) => {
    if (resetPasswordModal) {
        resetPasswordModal.classList.remove('hidden');
    }
    if (resetPasswordForm) {
        resetPasswordForm.reset();
    }
    if (resetQAGroup) {
        resetQAGroup.classList.add('hidden');
    }
    if (submitResetBtn) {
        submitResetBtn.classList.add('hidden');
    }

    if (isLoggedIn && currentUser) {
        if (resetUsernameInput) resetUsernameInput.value = currentUser.username;
        if (resetUsernameGroup) resetUsernameGroup.classList.add('hidden');
        if (resetGetQuestionBtn) resetGetQuestionBtn.classList.add('hidden');

        // Auto fetch question
        fetchSecurityQuestion(currentUser.username);
    } else {
        if (resetUsernameGroup) resetUsernameGroup.classList.remove('hidden');
        if (resetGetQuestionBtn) resetGetQuestionBtn.classList.remove('hidden');
        if (resetUsernameInput) resetUsernameInput.value = '';
    }
};

const hideResetModal = () => {
    if (resetPasswordModal) {
        resetPasswordModal.classList.add('hidden');
    }
};

if (closeResetModalBtn) closeResetModalBtn.addEventListener('click', hideResetModal);
if (cancelResetBtn) cancelResetBtn.addEventListener('click', hideResetModal);

async function fetchSecurityQuestion(username) {
    if (!username || username.trim() === '') {
        alert("Please enter a username.");
        return;
    }

    try {
        const response = await fetch(`/api/forgot-password/get-question?username=${encodeURIComponent(username)}`);
        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Failed to fetch security question.");
            return;
        }

        const data = await response.json();
        if (data.success) {
            if (resetQuestionText) resetQuestionText.textContent = data.question;
            if (resetQAGroup) resetQAGroup.classList.remove('hidden');
            if (submitResetBtn) submitResetBtn.classList.remove('hidden');
            if (resetGetQuestionBtn && !currentUser) {
                resetGetQuestionBtn.classList.add('hidden');
            }
        }
    } catch (err) {
        console.error(err);
        alert("Error connecting to server.");
    }
}

if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = resetUsernameInput ? resetUsernameInput.value.trim() : '';
        const answer = resetAnswerInput ? resetAnswerInput.value.trim() : '';
        const newPassword = resetNewPasswordInput ? resetNewPasswordInput.value : '';

        if (!username || !answer || !newPassword) {
            alert("All fields are required.");
            return;
        }

        try {
            const response = await fetch('/api/forgot-password/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    security_answer: answer,
                    new_password: newPassword
                })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail || "Failed to reset password.");
                return;
            }

            const data = await response.json();
            if (data.success) {
                alert("Password reset successfully! Please log in with your new password.");
                hideResetModal();
                // If logged in, logout user so they re-login
                if (currentUser) {
                    logoutUser();
                }
            }
        } catch (err) {
            console.error(err);
            alert("Error communicating with server.");
        }
    });
}

// --- Voice Phrase Reset Section ---
const resetVoiceModal = document.getElementById('reset-voice-modal');
const closeVoiceModalBtn = document.getElementById('close-voice-modal');
const cancelVoiceResetBtn = document.getElementById('cancel-voice-reset-btn');
const dropdownResetVoiceBtn = document.getElementById('dropdown-reset-voice-btn');
const resetVoiceForm = document.getElementById('reset-voice-form');
const dictateResetVoiceBtn = document.getElementById('dictate-reset-voice-btn');

const resetVoiceUsernameInput = document.getElementById('reset-voice-username');
const resetVoiceQuestionText = document.getElementById('reset-voice-question-text');
const resetVoiceAnswerInput = document.getElementById('reset-voice-answer');
const resetVoicePassphraseInput = document.getElementById('reset-voice-passphrase');
const resetVoiceEnrollmentBadge = document.getElementById('reset-voice-enrollment-badge');

const showResetVoiceModal = () => {
    if (resetVoiceModal) {
        resetVoiceModal.classList.remove('hidden');
    }
    if (resetVoiceForm) {
        resetVoiceForm.reset();
    }
    if (resetVoiceEnrollmentBadge) {
        resetVoiceEnrollmentBadge.className = 'voice-enrollment-badge';
        resetVoiceEnrollmentBadge.innerHTML = '';
    }
    resetVoiceAudioBase64 = null;
    resetVoiceAudioMime = null;

    if (currentUser) {
        if (resetVoiceUsernameInput) resetVoiceUsernameInput.value = currentUser.username;
        // Fetch security question
        fetchVoiceResetSecurityQuestion(currentUser.username);
    }
};

const hideResetVoiceModal = () => {
    if (resetVoiceModal) {
        resetVoiceModal.classList.add('hidden');
    }
    stopSpeechEngine();
};

if (dropdownResetVoiceBtn) dropdownResetVoiceBtn.addEventListener('click', () => {
    showResetVoiceModal();
    // Dismiss settings dropdown
    if (settingsDropdown) settingsDropdown.classList.add('hidden');
});

if (closeVoiceModalBtn) closeVoiceModalBtn.addEventListener('click', hideResetVoiceModal);
if (cancelVoiceResetBtn) cancelVoiceResetBtn.addEventListener('click', hideResetVoiceModal);

if (resetVoiceModal) {
    resetVoiceModal.addEventListener('click', (e) => {
        if (e.target === resetVoiceModal) {
            hideResetVoiceModal();
        }
    });
}

async function fetchVoiceResetSecurityQuestion(username) {
    try {
        const response = await fetch(`/api/forgot-password/get-question?username=${encodeURIComponent(username)}`);
        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Failed to fetch security question.");
            return;
        }

        const data = await response.json();
        if (data.success) {
            if (resetVoiceQuestionText) resetVoiceQuestionText.textContent = data.question;
        }
    } catch (err) {
        console.error(err);
        alert("Error connecting to server.");
    }
}

// Dictate button for Reset Voice Phrase modal
if (dictateResetVoiceBtn) {
    dictateResetVoiceBtn.addEventListener('click', async () => {
        if (!recognition) return;
        if (isResetVoiceRecording) {
            recognition.stop();
        } else {
            window.speechSynthesis.cancel();
            activeSpeechMode = 'dictate_reset_voice';
            isResetVoiceRecording = true;
            dictateResetVoiceBtn.classList.add('listening');

            if (resetVoiceEnrollmentBadge) {
                resetVoiceEnrollmentBadge.className = 'voice-enrollment-badge info';
                resetVoiceEnrollmentBadge.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Listening for passphrase...';
            }

            await startAudioRecording();
            recognition.lang = selectedLanguage;
            recognition.start();
        }
    });
}

function handleResetVoiceDictate(text, base64Audio) {
    if (!text || text.trim() === '') return;
    const phrase = text.replace(/[.!?]/g, '').trim().toLowerCase();
    if (resetVoicePassphraseInput) resetVoicePassphraseInput.value = phrase;

    resetVoiceAudioBase64 = base64Audio;
    resetVoiceAudioMime = voiceAudioMime;

    if (resetVoiceEnrollmentBadge) {
        resetVoiceEnrollmentBadge.className = 'voice-enrollment-badge success';
        resetVoiceEnrollmentBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> Voice print captured successfully!';
    }

    speakText(`Recorded passphrase and captured voice print successfully.`);
}

if (resetVoiceForm) {
    resetVoiceForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = resetVoiceUsernameInput ? resetVoiceUsernameInput.value.trim() : '';
        const answer = resetVoiceAnswerInput ? resetVoiceAnswerInput.value.trim() : '';
        const newPhrase = resetVoicePassphraseInput ? resetVoicePassphraseInput.value.trim() : '';

        if (!username || !answer || !newPhrase) {
            alert("All fields are required.");
            return;
        }

        // New voice print recording is optional, so we bypass this validation.

        try {
            const response = await fetch('/api/settings/reset-voice', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    security_answer: answer,
                    new_voice_phrase: newPhrase,
                    voice_audio_base64: resetVoiceAudioBase64,
                    voice_audio_mime: resetVoiceAudioMime
                })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail || "Failed to reset voice phrase.");
                return;
            }

            const data = await response.json();
            if (data.success) {
                alert("Voice phrase reset successfully!");
                hideResetVoiceModal();
            }
        } catch (err) {
            console.error(err);
            alert("Error communicating with server.");
        }
    });
}

// Toggle settings dropdown
const settingsBtn = document.getElementById('settings-btn');
const settingsDropdown = document.getElementById('settings-dropdown');

if (settingsBtn && settingsDropdown) {
    settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsDropdown.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
        if (!settingsDropdown.classList.contains('hidden')) {
            settingsDropdown.classList.add('hidden');
        }
    });
}

// Reset from Settings dropdown
if (dropdownResetBtn) {
    dropdownResetBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (settingsDropdown) settingsDropdown.classList.add('hidden');
        showResetModal(true);
    });
}

// Forgot Password link click
if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener('click', (e) => {
        e.preventDefault();
        showResetModal(false);
    });
}

// Fetch question button click
if (resetGetQuestionBtn) {
    resetGetQuestionBtn.addEventListener('click', () => {
        if (resetUsernameInput) {
            fetchSecurityQuestion(resetUsernameInput.value.trim());
        }
    });
}

// --- Quick Transfer / Payment Logic ---
async function populatePaymentRecipients(username) {
    const recipientSelect = document.getElementById('payment-recipient');
    if (!recipientSelect) return;

    const lang = selectedLanguage;
    const langData = translations[lang] || translations['en-IN'];
    const defaultText = langData['option-select-recipient'] || 'Select Recipient';
    recipientSelect.innerHTML = `<option value="" disabled selected>${defaultText}</option>`;

    try {
        const response = await fetch(`/api/users?exclude=${encodeURIComponent(username)}`);
        if (!response.ok) {
            console.error("Failed to load recipients list.");
            return;
        }

        const users = await response.json();
        users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.username;
            opt.textContent = `${u.name} (@${u.username})`;
            recipientSelect.appendChild(opt);
        });
    } catch (err) {
        console.error("Error fetching recipients:", err);
    }
}

const dashboardPaymentForm = document.getElementById('dashboard-payment-form');
if (dashboardPaymentForm) {
    dashboardPaymentForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!currentUser) {
            alert("You must be logged in.");
            return;
        }

        const recipient = document.getElementById('payment-recipient').value;
        const source = document.getElementById('payment-source').value;
        const amount = parseFloat(document.getElementById('payment-amount').value);
        const mpin = document.getElementById('payment-mpin').value;

        if (!recipient || !source || isNaN(amount) || amount <= 0 || !mpin) {
            alert("Please complete all payment fields.");
            return;
        }

        try {
            const response = await fetch('/api/payments/transfer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: currentUser.username,
                    recipient_username: recipient,
                    amount: amount,
                    source_account: source,
                    mpin: mpin
                })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail || "Payment failed.");
                return;
            }

            const data = await response.json();
            if (data.success) {
                alert(data.message || "Payment completed successfully!");
                speakText(data.message || "Payment completed successfully.");

                // Reset form fields
                document.getElementById('payment-amount').value = '';
                document.getElementById('payment-mpin').value = '';
                document.getElementById('payment-recipient').value = '';

                // Refresh dashboard info
                fetchInitialState(currentUser.username);
            }
        } catch (err) {
            console.error(err);
            alert("Error connecting to banking server.");
        }
    });
}

// --- Analytics & Charts Dashboard Logic ---

// Chart instances
let spendingTrendChart = null;
let spendingCategoryChart = null;
let incomeExpenseChart = null;

// Tab bindings & Multi-page Routing Logic
const tabSummaryBtn = document.getElementById('tab-summary-btn');
const tabAnalyticsBtn = document.getElementById('tab-analytics-btn');
const tabVoiceBtn = document.getElementById('tab-voice-btn');
const tabKnowledgeBtn = document.getElementById('tab-knowledge-btn');

const mainDashboardView = document.getElementById('main-dashboard-view');
const analyticsDashboardView = document.getElementById('analytics-dashboard-view');
const voiceTransactionDashboardView = document.getElementById('voice-transaction-dashboard-view');
const knowledgeDashboardView = document.getElementById('knowledge-dashboard-view');

const floatingMicBtn = document.getElementById('floating-mic-btn');

function updateFloatingMicVisibility() {
    if (!currentUser) {
        if (floatingMicBtn) floatingMicBtn.classList.add('hidden');
        return;
    }
    if (tabVoiceBtn && tabVoiceBtn.classList.contains('active')) {
        if (floatingMicBtn) floatingMicBtn.classList.add('hidden');
    } else {
        if (floatingMicBtn) floatingMicBtn.classList.remove('hidden');
    }
}

function switchDashboardTab(activeTabId) {
    const tabs = [
        { btn: tabSummaryBtn, view: mainDashboardView },
        { btn: tabAnalyticsBtn, view: analyticsDashboardView },
        { btn: tabVoiceBtn, view: voiceTransactionDashboardView },
        { btn: tabKnowledgeBtn, view: knowledgeDashboardView }
    ];

    tabs.forEach(t => {
        if (t.btn && t.view) {
            if (t.btn.id === activeTabId) {
                t.btn.classList.add('active');
                t.view.classList.remove('hidden');
            } else {
                t.btn.classList.remove('active');
                t.view.classList.add('hidden');
            }
        }
    });

    if (activeTabId === 'tab-analytics-btn') {
        renderAnalytics();
    }

    updateFloatingMicVisibility();
}

if (tabSummaryBtn) tabSummaryBtn.addEventListener('click', () => switchDashboardTab('tab-summary-btn'));
if (tabAnalyticsBtn) tabAnalyticsBtn.addEventListener('click', () => switchDashboardTab('tab-analytics-btn'));
if (tabVoiceBtn) tabVoiceBtn.addEventListener('click', () => switchDashboardTab('tab-voice-btn'));
if (tabKnowledgeBtn) tabKnowledgeBtn.addEventListener('click', () => switchDashboardTab('tab-knowledge-btn'));

// Floating Action Button Listener
if (floatingMicBtn) {
    floatingMicBtn.addEventListener('click', () => {
        switchDashboardTab('tab-voice-btn');
        // Let user speech trigger mic activation
        if (micBtn && !isRecording) {
            setTimeout(() => {
                micBtn.click();
            }, 150);
        }
    });
}

// Suggested prompt buttons click binding (Knowledge page)
document.querySelectorAll('.k-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        let cmd = btn.getAttribute('data-command');
        if (!cmd) {
            cmd = btn.innerText.replace(/"/g, '').trim();
        }
        if (cmd) {
            switchDashboardTab('tab-voice-btn');
            handleUserSpeech(cmd);
        }
    });
});



// Voice Page pdf statement download listener
const voiceStatementModalBtn = document.getElementById('voice-statement-modal-btn');
if (voiceStatementModalBtn) {
    voiceStatementModalBtn.addEventListener('click', () => {
        statementModal.classList.remove('hidden');
        statementForm.reset();
        dateRangeInputs.classList.add('hidden');
        statementStartDate.value = '';
        statementEndDate.value = '';
    });
}

// Support Desk Query Form Form submission listener
const knowledgeQueryForm = document.getElementById('knowledge-query-form');
const kQueryInput = document.getElementById('k-query-input');
const kResponseBox = document.getElementById('k-response-box');
const kResponseBody = document.getElementById('k-response-body');

if (knowledgeQueryForm) {
    knowledgeQueryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = kQueryInput.value.trim();
        if (!text || !currentUser) return;

        kResponseBox.classList.remove('hidden');
        kResponseBody.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Support Specialist is processing...';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: text,
                    username: currentUser.username,
                    language: selectedLanguage
                })
            });

            if (response.ok) {
                const data = await response.json();
                kResponseBody.innerHTML = formatAssistantResponse(data.response);
                speakText(data.response);
                updateDashboard(data.state);
            } else {
                kResponseBody.textContent = "Error communicating with NidhiVani AI server.";
            }
        } catch (err) {
            console.error(err);
            kResponseBody.textContent = "Unable to connect to the banking support server.";
        }
    });
}

// Filter inputs bindings
const durationFilter = document.getElementById('chart-duration-filter');
const customDateFilters = document.getElementById('custom-date-filters');
const chartStartDate = document.getElementById('chart-start-date');
const chartEndDate = document.getElementById('chart-end-date');
const categoryFilter = document.getElementById('chart-category-filter');
const typeFilter = document.getElementById('chart-type-filter');
const resetAnalyticsFiltersBtn = document.getElementById('reset-analytics-filters-btn');

if (durationFilter) {
    durationFilter.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            customDateFilters.classList.remove('hidden');
        } else {
            customDateFilters.classList.add('hidden');
        }
        renderAnalytics();
    });
}

if (chartStartDate) chartStartDate.addEventListener('change', renderAnalytics);
if (chartEndDate) chartEndDate.addEventListener('change', renderAnalytics);
if (categoryFilter) categoryFilter.addEventListener('change', renderAnalytics);
if (typeFilter) typeFilter.addEventListener('change', renderAnalytics);

if (resetAnalyticsFiltersBtn) {
    resetAnalyticsFiltersBtn.addEventListener('click', () => {
        if (durationFilter) durationFilter.value = '30';
        if (customDateFilters) customDateFilters.classList.add('hidden');
        if (chartStartDate) chartStartDate.value = '';
        if (chartEndDate) chartEndDate.value = '';
        if (categoryFilter) categoryFilter.value = 'all';
        if (typeFilter) typeFilter.value = 'all';
        renderAnalytics();
    });
}

// Date helper to parse text dates like "YYYY-MM-DD HH:MM"
function parseTransactionDate(dateStr) {
    if (!dateStr) return new Date();
    // Replace space with T to form ISO format for standard parser
    const cleanStr = dateStr.replace(' ', 'T');
    return new Date(cleanStr);
}

// Generate analytics metrics and render charts
function renderAnalytics() {
    if (!currentUser || !activeTransactions || activeTransactions.length === 0) {
        return;
    }

    const durationVal = durationFilter ? durationFilter.value : '30';
    const categoryVal = categoryFilter ? categoryFilter.value : 'all';
    const typeVal = typeFilter ? typeFilter.value : 'all';

    const now = new Date();
    let startDate = null;
    let endDate = null;

    if (durationVal !== 'all' && durationVal !== 'custom') {
        const days = parseInt(durationVal, 10);
        startDate = new Date();
        startDate.setDate(now.getDate() - days);
    } else if (durationVal === 'custom') {
        const startVal = chartStartDate ? chartStartDate.value : '';
        const endVal = chartEndDate ? chartEndDate.value : '';
        if (startVal) {
            startDate = new Date(startVal);
            startDate.setHours(0, 0, 0, 0);
        }
        if (endVal) {
            endDate = new Date(endVal);
            endDate.setHours(23, 59, 59, 999);
        }
    }

    // 1. Filter transactions
    const filteredTxs = activeTransactions.filter(tx => {
        // Date check
        const txDate = parseTransactionDate(tx.date);
        if (startDate && txDate < startDate) return false;
        if (endDate && txDate > endDate) return false;

        // Category check
        if (categoryVal !== 'all' && tx.category !== categoryVal) return false;

        // Type check
        if (typeVal !== 'all' && tx.type !== typeVal) return false;

        return true;
    });

    // 2. Compute metrics
    let totalIncome = 0;
    let totalSpending = 0;

    filteredTxs.forEach(tx => {
        if (tx.type.toLowerCase() === 'credit') {
            totalIncome += tx.amount;
        } else if (tx.type.toLowerCase() === 'debit') {
            totalSpending += tx.amount;
        }
    });

    const netSavings = totalIncome - totalSpending;
    const txCount = filteredTxs.length;

    // Update metrics UI
    const totalIncomeEl = document.getElementById('metric-total-income');
    const totalExpenseEl = document.getElementById('metric-total-expense');
    const netSavingsEl = document.getElementById('metric-net-savings');
    const txCountEl = document.getElementById('metric-tx-count');

    if (totalIncomeEl) totalIncomeEl.textContent = `₹${totalIncome.toFixed(2)}`;
    if (totalExpenseEl) totalExpenseEl.textContent = `₹${totalSpending.toFixed(2)}`;

    if (netSavingsEl) {
        netSavingsEl.textContent = `₹${netSavings.toFixed(2)}`;
        if (netSavings >= 0) {
            netSavingsEl.className = 'metric-value credit';
        } else {
            netSavingsEl.className = 'metric-value debit';
        }
    }
    if (txCountEl) txCountEl.textContent = txCount;

    // 3. Render charts
    renderSpendingTrendChart(filteredTxs);
    renderSpendingCategoryChart(filteredTxs);
    renderIncomeExpenseComparisonChart(filteredTxs);
}

// Chart 1: Spending Trend over Time (Line Chart)
function renderSpendingTrendChart(transactions) {
    const canvas = document.getElementById('spending-trend-chart');
    if (!canvas) return;

    if (spendingTrendChart) {
        spendingTrendChart.destroy();
    }

    // Filter to Debits (Spendings) and sort by date chronologically
    const debits = transactions
        .filter(tx => tx.type.toLowerCase() === 'debit')
        .map(tx => ({
            dateStr: tx.date.substring(0, 10),
            amount: tx.amount
        }))
        .sort((a, b) => a.dateStr.localeCompare(b.dateStr));

    if (debits.length === 0) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#64748b';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No spending data for the selected filters', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Aggregate by date (daily total spending) and then compute cumulative spending
    const dailySpendingMap = {};
    debits.forEach(d => {
        dailySpendingMap[d.dateStr] = (dailySpendingMap[d.dateStr] || 0) + d.amount;
    });

    const uniqueDates = Object.keys(dailySpendingMap).sort();
    let cumulativeSum = 0;
    const cumulativeData = uniqueDates.map(date => {
        cumulativeSum += dailySpendingMap[date];
        return cumulativeSum;
    });

    const ctx = canvas.getContext('2d');

    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(2, 132, 199, 0.3)');
    gradient.addColorStop(1, 'rgba(2, 132, 199, 0.0)');

    spendingTrendChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: uniqueDates,
            datasets: [{
                label: 'Cumulative Spending (₹)',
                data: cumulativeData,
                borderColor: '#0284c7',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#0284c7',
                pointBorderColor: '#ffffff',
                pointHoverRadius: 7,
                pointRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `Total Spent: ₹${context.raw.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#64748b'
                    }
                },
                y: {
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#64748b',
                        callback: function (value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });
}

// Chart 2: Spending by Category (Doughnut Chart)
function renderSpendingCategoryChart(transactions) {
    const canvas = document.getElementById('spending-category-chart');
    if (!canvas) return;

    if (spendingCategoryChart) {
        spendingCategoryChart.destroy();
    }

    // Filter to Debits (Spendings) and group by category
    const debits = transactions.filter(tx => tx.type.toLowerCase() === 'debit');

    const categoryMap = {};
    debits.forEach(tx => {
        const cat = tx.category || 'Other';
        categoryMap[cat] = (categoryMap[cat] || 0) + tx.amount;
    });

    const categories = Object.keys(categoryMap);
    const amounts = Object.values(categoryMap);

    if (categories.length === 0) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#64748b';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No spending data for the selected filters', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Color palette
    const colors = [
        '#0284c7', // cyan
        '#4f46e5', // indigo
        '#a855f7', // purple
        '#f59e0b', // amber
        '#e11d48', // rose
        '#0d9488', // teal
        '#2563eb', // blue
        '#64748b'  // slate
    ];

    spendingCategoryChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: colors.slice(0, categories.length),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        font: { family: 'Inter', size: 11, weight: '600' },
                        color: '#475569',
                        padding: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const val = context.raw;
                            const percentage = ((val / total) * 100).toFixed(1);
                            return ` ${context.label}: ₹${val.toFixed(2)} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// Chart 3: Income vs Expenses Comparison (Grouped Bar Chart)
function renderIncomeExpenseComparisonChart(transactions) {
    const canvas = document.getElementById('income-expense-chart');
    if (!canvas) return;

    if (incomeExpenseChart) {
        incomeExpenseChart.destroy();
    }

    // Group credits and debits by date
    const dailyData = {}; // { "YYYY-MM-DD": { credit: 0, debit: 0 } }

    transactions.forEach(tx => {
        const dateStr = tx.date.substring(0, 10);
        if (!dailyData[dateStr]) {
            dailyData[dateStr] = { credit: 0, debit: 0 };
        }
        if (tx.type.toLowerCase() === 'credit') {
            dailyData[dateStr].credit += tx.amount;
        } else if (tx.type.toLowerCase() === 'debit') {
            dailyData[dateStr].debit += tx.amount;
        }
    });

    const dates = Object.keys(dailyData).sort();
    const credits = dates.map(d => dailyData[d].credit);
    const debits = dates.map(d => dailyData[d].debit);

    if (dates.length === 0) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#64748b';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No data available for comparison', canvas.width / 2, canvas.height / 2);
        return;
    }

    incomeExpenseChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Income (₹)',
                    data: credits,
                    backgroundColor: '#16a34a',
                    borderRadius: 4
                },
                {
                    label: 'Expenses (₹)',
                    data: debits,
                    backgroundColor: '#dc2626',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: { family: 'Inter', size: 11, weight: '600' },
                        color: '#475569'
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#64748b'
                    }
                },
                y: {
                    grid: {
                        color: '#f1f5f9'
                    },
                    ticks: {
                        font: { family: 'Inter', size: 10 },
                        color: '#64748b',
                        callback: function (value) {
                            return '₹' + value;
                        }
                    }
                }
            }
        }
    });
}

// ==========================================
// Face Recognition Feature Implementation
// ==========================================

// 1. Helper function to capture base64 JPEG from video/canvas
function getBase64Image(video, canvas) {
    const ctx = canvas.getContext('2d');
    // Draw current video frame onto canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    // Return base64 representation of the image
    const dataUrl = canvas.toDataURL('image/jpeg');
    return dataUrl.split(',')[1]; // Return only the raw base64 string
}

// 2. Registration Webcam Controller
faceRegisterCameraToggleBtn.addEventListener('click', async () => {
    if (faceRegisterStream) {
        // Stop the camera
        stopRegisterCamera();
    } else {
        // Start the camera
        try {
            faceRegisterStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 320, height: 240, facingMode: 'user' }
            });
            faceRegisterVideo.srcObject = faceRegisterStream;
            faceRegisterCameraContainer.style.display = 'block';
            faceRegisterCaptureBtn.classList.remove('hidden');
            faceRegisterCameraToggleBtn.innerHTML = '<i class="fa-solid fa-video-slash"></i> Stop Camera';
            faceRegisterStatus.textContent = 'Camera active. Center your face and capture.';
            faceRegisterStatus.className = 'face-enrollment-badge';
        } catch (err) {
            console.error("Webcam access error:", err);
            faceRegisterStatus.textContent = 'Failed to access camera. Check permissions.';
            faceRegisterStatus.className = 'face-enrollment-badge error';
        }
    }
});

function stopRegisterCamera() {
    if (faceRegisterStream) {
        faceRegisterStream.getTracks().forEach(track => track.stop());
        faceRegisterStream = null;
    }
    faceRegisterVideo.srcObject = null;
    faceRegisterCameraContainer.style.display = 'none';
    faceRegisterCaptureBtn.classList.add('hidden');
    faceRegisterCameraToggleBtn.innerHTML = '<i class="fa-solid fa-video"></i> Start Camera';
}

faceRegisterCaptureBtn.addEventListener('click', () => {
    try {
        capturedFaceBase64 = getBase64Image(faceRegisterVideo, faceRegisterCanvas);
        faceRegisterStatus.textContent = 'Face scan captured successfully!';
        faceRegisterStatus.className = 'face-enrollment-badge success';
        stopRegisterCamera();
    } catch (err) {
        console.error("Face capture error:", err);
        faceRegisterStatus.textContent = 'Failed to capture face frame.';
        faceRegisterStatus.className = 'face-enrollment-badge error';
    }
});

// 3. Login Webcam Controller
let faceLoginAutoTimeout = null;
let faceLoginCountdownInterval = null;

// 3. Login Webcam Controller
faceLoginCameraToggleBtn.addEventListener('click', async () => {
    if (faceLoginStream) {
        stopLoginCamera();
    } else {
        try {
            faceLoginStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 320, height: 240, facingMode: 'user' }
            });
            faceLoginVideo.srcObject = faceLoginStream;
            faceLoginCameraContainer.style.display = 'block';
            faceLoginCameraToggleBtn.innerHTML = '<i class="fa-solid fa-camera-slash"></i>';
            faceLoginCameraToggleBtn.parentElement.classList.add('scanning');
            
            // Start automatic 2-second countdown for scan
            let secondsLeft = 2;
            faceLoginStatus.textContent = `Camera active. Aligning face... scanning in ${secondsLeft} seconds...`;
            faceLoginStatus.className = 'face-login-status processing';
            
            faceLoginCountdownInterval = setInterval(() => {
                secondsLeft--;
                if (secondsLeft > 0) {
                    faceLoginStatus.textContent = `Camera active. Aligning face... scanning in ${secondsLeft} second${secondsLeft > 1 ? 's' : ''}...`;
                } else {
                    clearInterval(faceLoginCountdownInterval);
                }
            }, 1000);
            
            faceLoginAutoTimeout = setTimeout(async () => {
                clearInterval(faceLoginCountdownInterval);
                await triggerAutoFaceLogin();
            }, 2000);
            
        } catch (err) {
            console.error("Webcam access error:", err);
            faceLoginStatus.textContent = 'Failed to access camera.';
            faceLoginStatus.className = 'face-login-status error';
        }
    }
});

function stopLoginCamera() {
    if (faceLoginCountdownInterval) {
        clearInterval(faceLoginCountdownInterval);
        faceLoginCountdownInterval = null;
    }
    if (faceLoginAutoTimeout) {
        clearTimeout(faceLoginAutoTimeout);
        faceLoginAutoTimeout = null;
    }
    if (faceLoginStream) {
        faceLoginStream.getTracks().forEach(track => track.stop());
        faceLoginStream = null;
    }
    faceLoginVideo.srcObject = null;
    faceLoginCameraContainer.style.display = 'none';
    faceLoginCaptureBtn.classList.add('hidden');
    faceLoginCameraToggleBtn.innerHTML = '<i class="fa-solid fa-camera"></i>';
    faceLoginCameraToggleBtn.parentElement.classList.remove('scanning');
}

async function triggerAutoFaceLogin() {
    faceLoginStatus.textContent = 'Analyzing face patterns... Please hold still...';
    faceLoginStatus.className = 'face-login-status processing';

    try {
        const liveFaceBase64 = getBase64Image(faceLoginVideo, faceLoginCanvas);
        
        const response = await fetch('/api/face-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                face_image_base64: liveFaceBase64
            })
        });

        if (!response.ok) {
            const err = await response.json();
            faceLoginStatus.textContent = err.detail || 'Face verification failed.';
            faceLoginStatus.className = 'face-login-status error';
            stopLoginCamera();
            return;
        }

        const data = await response.json();
        if (data.success) {
            faceLoginStatus.textContent = 'Authentication successful!';
            faceLoginStatus.className = 'face-login-status success';
            stopLoginCamera();
            
            // Login user to the dashboard
            loginUser(data.username, data.name);
        } else {
            faceLoginStatus.textContent = data.message || 'Face match failed.';
            faceLoginStatus.className = 'face-login-status error';
            stopLoginCamera();
        }
    } catch (err) {
        console.error("Face login error:", err);
        faceLoginStatus.textContent = 'Server communication error during face login.';
        faceLoginStatus.className = 'face-login-status error';
        stopLoginCamera();
    }
}

// --- Reset Face Scan Section ---
const resetFaceModal = document.getElementById('reset-face-modal');
const closeFaceModalBtn = document.getElementById('close-face-modal');
const cancelFaceResetBtn = document.getElementById('cancel-face-reset-btn');
const dropdownResetFaceBtn = document.getElementById('dropdown-reset-face-btn');
const resetFaceForm = document.getElementById('reset-face-form');

const resetFaceUsernameInput = document.getElementById('reset-face-username');
const resetFaceQuestionText = document.getElementById('reset-face-question-text');
const resetFaceAnswerInput = document.getElementById('reset-face-answer');
const resetFaceStatus = document.getElementById('reset-face-status');
const resetFaceCameraContainer = document.getElementById('reset-face-camera-container');
const resetFaceVideo = document.getElementById('reset-face-video');
const resetFaceCanvas = document.getElementById('reset-face-canvas');
const resetFaceCameraToggleBtn = document.getElementById('reset-face-camera-toggle-btn');
const resetFaceCaptureBtn = document.getElementById('reset-face-capture-btn');

let resetFaceStream = null;
let capturedResetFaceBase64 = null;

const showResetFaceModal = () => {
    if (resetFaceModal) {
        resetFaceModal.classList.remove('hidden');
    }
    if (resetFaceForm) {
        resetFaceForm.reset();
    }
    if (resetFaceStatus) {
        resetFaceStatus.textContent = 'No face scanned yet';
        resetFaceStatus.className = 'face-enrollment-badge';
    }
    capturedResetFaceBase64 = null;

    if (currentUser) {
        if (resetFaceUsernameInput) resetFaceUsernameInput.value = currentUser.username;
        // Fetch security question
        fetchFaceResetSecurityQuestion(currentUser.username);
    }
};

const hideResetFaceModal = () => {
    if (resetFaceModal) {
        resetFaceModal.classList.add('hidden');
    }
    stopResetFaceCamera();
};

if (dropdownResetFaceBtn) dropdownResetFaceBtn.addEventListener('click', () => {
    showResetFaceModal();
    // Dismiss settings dropdown
    if (settingsDropdown) settingsDropdown.classList.add('hidden');
});

if (closeFaceModalBtn) closeFaceModalBtn.addEventListener('click', hideResetFaceModal);
if (cancelFaceResetBtn) cancelFaceResetBtn.addEventListener('click', hideResetFaceModal);

if (resetFaceModal) {
    resetFaceModal.addEventListener('click', (e) => {
        if (e.target === resetFaceModal) {
            hideResetFaceModal();
        }
    });
}

async function fetchFaceResetSecurityQuestion(username) {
    try {
        const response = await fetch(`/api/forgot-password/get-question?username=${encodeURIComponent(username)}`);
        if (!response.ok) {
            const err = await response.json();
            alert(err.detail || "Failed to fetch security question.");
            return;
        }

        const data = await response.json();
        if (data.success) {
            if (resetFaceQuestionText) resetFaceQuestionText.textContent = data.question;
        }
    } catch (err) {
        console.error(err);
        alert("Error connecting to server.");
    }
}

// Reset Face Webcam Controller
if (resetFaceCameraToggleBtn) {
    resetFaceCameraToggleBtn.addEventListener('click', async () => {
        if (resetFaceStream) {
            stopResetFaceCamera();
        } else {
            try {
                resetFaceStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 320, height: 240, facingMode: 'user' }
                });
                resetFaceVideo.srcObject = resetFaceStream;
                resetFaceCameraContainer.style.display = 'block';
                resetFaceCaptureBtn.classList.remove('hidden');
                resetFaceCameraToggleBtn.innerHTML = '<i class="fa-solid fa-video-slash"></i> Stop Camera';
                resetFaceStatus.textContent = 'Camera active. Center your face and capture.';
                resetFaceStatus.className = 'face-enrollment-badge';
            } catch (err) {
                console.error("Webcam access error:", err);
                resetFaceStatus.textContent = 'Failed to access camera. Check permissions.';
                resetFaceStatus.className = 'face-enrollment-badge error';
            }
        }
    });
}

function stopResetFaceCamera() {
    if (resetFaceStream) {
        resetFaceStream.getTracks().forEach(track => track.stop());
        resetFaceStream = null;
    }
    if (resetFaceVideo) resetFaceVideo.srcObject = null;
    if (resetFaceCameraContainer) resetFaceCameraContainer.style.display = 'none';
    if (resetFaceCaptureBtn) resetFaceCaptureBtn.classList.add('hidden');
    if (resetFaceCameraToggleBtn) resetFaceCameraToggleBtn.innerHTML = '<i class="fa-solid fa-video"></i> Start Camera';
}

if (resetFaceCaptureBtn) {
    resetFaceCaptureBtn.addEventListener('click', () => {
        try {
            capturedResetFaceBase64 = getBase64Image(resetFaceVideo, resetFaceCanvas);
            resetFaceStatus.textContent = 'Face scan captured successfully!';
            resetFaceStatus.className = 'face-enrollment-badge success';
            stopResetFaceCamera();
        } catch (err) {
            console.error("Face capture error:", err);
            resetFaceStatus.textContent = 'Failed to capture face frame.';
            resetFaceStatus.className = 'face-enrollment-badge error';
        }
    });
}

if (resetFaceForm) {
    resetFaceForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = resetFaceUsernameInput ? resetFaceUsernameInput.value.trim() : '';
        const answer = resetFaceAnswerInput ? resetFaceAnswerInput.value.trim() : '';

        if (!username || !answer) {
            alert("All fields are required.");
            return;
        }

        if (!capturedResetFaceBase64) {
            alert("Please capture a face scan first.");
            return;
        }

        try {
            const response = await fetch('/api/settings/reset-face', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: username,
                    security_answer: answer,
                    face_image_base64: capturedResetFaceBase64
                })
            });

            if (!response.ok) {
                const err = await response.json();
                alert(err.detail || "Failed to update face scan.");
                return;
            }

            const data = await response.json();
            if (data.success) {
                alert("Face scan updated successfully!");
                hideResetFaceModal();
            }
        } catch (err) {
            console.error(err);
            alert("Error updating face scan.");
        }
    });
}


