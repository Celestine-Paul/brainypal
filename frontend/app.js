// BrainyPal - Main Application Logic
// app.js

// Global application state
let appState = {
    user: null,
    currentTab: 'generate',
    studyData: {
        flashcards: [],
        quizQuestions: [],
        progress: {
            totalCards: 0,
            cardsStudied: 0,
            correctAnswers: 0,
            totalQuestions: 0,
            streak: 0,
            studyTime: 0,
            topicsStudied: 0
        },
        recentActivity: []
    },
    session: {
        startTime: null,
        isActive: false,
        timer: null
    },
    limits: {
        free: {
            dailyGenerations: 5,
            maxCards: 10,
            maxQuestions: 5
        },
        premium: {
            dailyGenerations: -1, // unlimited
            maxCards: 50,
            maxQuestions: 25
        }
    },
    usage: {
        today: 0,
        lastReset: new Date().toDateString()
    }
};

// API Configuration
const API_CONFIG = {
    baseURL: 'http://localhost:5000/api',  // Flask backend URL
    endpoints: {
        auth: '/auth',
        generate: '/generate',
        progress: '/progress',
        payment: '/payment'
    }
};

// Initialize Application
function initializeApp() {
    console.log('🧠 Initializing BrainyPal...');
    
    // Show loading screen
    showLoadingScreen();
    
    // Check authentication
    setTimeout(() => {
        checkAuthentication();
        hideLoadingScreen();
        createFloatingParticles();
        resetDailyUsage();
        loadSampleData(); // For demo purposes
    }, 2000);
}

// Loading Screen Functions
function showLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.display = 'flex';
    }
}

function hideLoadingScreen() {
    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        loadingScreen.style.opacity = '0';
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);
    }
}

// Authentication Check
function checkAuthentication() {
    const token = localStorage.getItem('brainypal_token');
    const userData = localStorage.getItem('brainypal_user');
    
    if (token && userData) {
        // User is logged in
        appState.user = JSON.parse(userData);
        showMainApp();
        updateUserInterface();
        loadUserData();
    } else {
        // User needs to log in
        showAuthModal();
    }
}

function showMainApp() {
    document.getElementById('authOverlay').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
}

function showAuthModal() {
    document.getElementById('authOverlay').style.display = 'flex';
    document.getElementById('mainApp').style.display = 'none';
}

// Tab Management
function switchTab(tabName) {
    // Update active states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Activate selected tab
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    appState.currentTab = tabName;
    
    // Load tab-specific content
    switch(tabName) {
        case 'flashcards':
            renderFlashcards();
            break;
        case 'quiz':
            renderQuiz();
            break;
        case 'progress':
            updateProgressDisplay();
            break;
        case 'analytics':
            loadAnalytics();
            break;
        case 'pricing':
            updatePricingDisplay();
            break;
    }
}

// Input Method Selection
function selectInputMethod(method) {
    // Update UI
    document.querySelectorAll('.input-method').forEach(el => {
        el.classList.remove('active');
    });
    event.target.closest('.input-method').classList.add('active');
    
    // Show/hide input areas
    document.getElementById('textInput').style.display = method === 'text' ? 'block' : 'none';
    document.getElementById('fileInput').style.display = method === 'file' ? 'block' : 'none';
}

// File Upload Handling
function handleFileUpload(event) {
    const files = Array.from(event.target.files);
    const uploadedFilesContainer = document.getElementById('uploadedFiles');
    
    files.forEach((file, index) => {
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            showNotification('File too large. Please select files under 10MB.', 'error');
            return;
        }
        
        const fileItem = createFileItem(file, index);
        uploadedFilesContainer.appendChild(fileItem);
    });
    
    // Clear the file input
    event.target.value = '';
}

function createFileItem(file, index) {
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <span class="file-icon">${getFileIcon(file.type)}</span>
        <div class="file-info">
            <div class="file-name">${file.name}</div>
            <div class="file-size">${formatFileSize(file.size)}</div>
        </div>
        <span class="remove-file" onclick="removeFile(this)">&times;</span>
    `;
    return fileItem;
}

function getFileIcon(fileType) {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('text')) return '📄';
    return '📁';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removeFile(element) {
    element.parentElement.remove();
}

// Study Materials Generation
async function generateStudyMaterials() {
    if (!canGenerate()) {
        showUsageLimit();
        return;
    }
    
    const formData = collectFormData();
    if (!validateFormData(formData)) {
        return;
    }
    
    showGeneratingState();
    
    try {
        const response = await generateWithAI(formData);
        
        if (response.success) {
            addGeneratedContent(response.data);
            updateUsage();
            showSuccess('Study materials generated successfully! 🎉');
            clearForm();
            addActivity('Generated new study materials', 'generate');
        } else {
            throw new Error(response.error);
        }
    } catch (error) {
        console.error('Generation error:', error);
        showNotification('Failed to generate materials. Please try again.', 'error');
    } finally {
        hideGeneratingState();
    }
}

function collectFormData() {
    const activeMethod = document.querySelector('.input-method.active');
    const isTextInput = activeMethod && activeMethod.onclick.toString().includes('text');
    
    return {
        method: isTextInput ? 'text' : 'file',
        content: isTextInput ? document.getElementById('studyNotes').value.trim() : null,
        files: isTextInput ? null : Array.from(document.querySelectorAll('.file-item')),
        topic: document.getElementById('topicName').value.trim(),
        settings: {
            difficulty: document.getElementById('difficultyLevel').value,
            cardCount: parseInt(document.getElementById('cardCount').value),
            questionCount: parseInt(document.getElementById('questionCount').value),
            contentType: document.getElementById('contentType').value
        }
    };
}

function validateFormData(data) {
    if (!data.topic) {
        showNotification('Please enter a topic name.', 'error');
        return false;
    }
    
    if (data.method === 'text' && !data.content) {
        showNotification('Please enter some study notes.', 'error');
        return false;
    }
    
    if (data.method === 'file' && (!data.files || data.files.length === 0)) {
        showNotification('Please upload at least one file.', 'error');
        return false;
    }
    
    return true;
}

function canGenerate() {
    const userPlan = appState.user?.subscription || 'free';
    const limit = appState.limits[userPlan].dailyGenerations;
    
    return limit === -1 || appState.usage.today < limit;
}

function showUsageLimit() {
    document.getElementById('usageLimit').style.display = 'block';
}

function hideUsageLimit() {
    document.getElementById('usageLimit').style.display = 'none';
}

function showGeneratingState() {
    const btn = document.getElementById('generateBtn');
    const spinner = document.getElementById('loadingSpinner');
    
    btn.disabled = true;
    spinner.style.display = 'inline-block';
    btn.innerHTML = '<div class="loading-spinner"></div>🤖 AI is Processing...';
}

function hideGeneratingState() {
    const btn = document.getElementById('generateBtn');
    const spinner = document.getElementById('loadingSpinner');
    
    btn.disabled = false;
    spinner.style.display = 'none';
    btn.innerHTML = '✨ Generate Study Materials';
}

// AI Integration (connects to backend)
async function generateWithAI(formData) {
    const endpoint = `${API_CONFIG.baseURL}${API_CONFIG.endpoints.generate}`;
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('brainypal_token')}`
            },
            body: JSON.stringify(formData)
        });
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        // Fallback to mock data for demo
        return await generateMockContent(formData);
    }
}

// Mock content generation for demo purposes
async function generateMockContent(formData) {
    await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API delay
    
    const mockFlashcards = [
        {
            id: Date.now(),
            question: `What is the main concept of ${formData.topic}?`,
            answer: `${formData.topic} is a fundamental concept that involves key principles and applications in its field.`,
            difficulty: formData.settings.difficulty,
            topic: formData.topic,
            created: new Date()
        },
        {
            id: Date.now() + 1,
            question: `How does ${formData.topic} apply in practice?`,
            answer: `Practical applications of ${formData.topic} include real-world implementations and problem-solving scenarios.`,
            difficulty: formData.settings.difficulty,
            topic: formData.topic,
            created: new Date()
        }
    ];
    
    const mockQuestions = [
        {
            id: Date.now(),
            question: `Which statement best describes ${formData.topic}?`,
            options: [
                'It is primarily theoretical',
                'It has practical applications',
                'It is outdated',
                'It is too complex to understand'
            ],
            correctAnswer: 1,
            topic: formData.topic,
            difficulty: formData.settings.difficulty
        }
    ];
    
    return {
        success: true,
        data: {
            flashcards: mockFlashcards.slice(0, formData.settings.cardCount),
            questions: mockQuestions.slice(0, formData.settings.questionCount)
        }
    };
}

function addGeneratedContent(data) {
    appState.studyData.flashcards.push(...data.flashcards);
    appState.studyData.quizQuestions.push(...data.questions);
    appState.studyData.progress.totalCards = appState.studyData.flashcards.length;
    appState.studyData.progress.topicsStudied++;
    
    saveUserData();
}

function updateUsage() {
    appState.usage.today++;
    localStorage.setItem('brainypal_usage', JSON.stringify(appState.usage));
}

function resetDailyUsage() {
    const today = new Date().toDateString();
    if (appState.usage.lastReset !== today) {
        appState.usage.today = 0;
        appState.usage.lastReset = today;
        localStorage.setItem('brainypal_usage', JSON.stringify(appState.usage));
    }
}

function clearForm() {
    document.getElementById('studyNotes').value = '';
    document.getElementById('topicName').value = '';
    document.getElementById('uploadedFiles').innerHTML = '';
}

// Flashcards Management
function renderFlashcards() {
    const container = document.getElementById('flashcardsContainer');
    const flashcards = appState.studyData.flashcards;
    
    if (flashcards.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🃏</div>
                <h3>No Flashcards Yet</h3>
                <p>Generate some study materials first to see your flashcards here!</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = flashcards.map((card, index) => `
        <div class="flashcard" onclick="flipCard(${index})" data-card-id="${card.id}">
            <div class="difficulty-badge difficulty-${card.difficulty}">${card.difficulty.toUpperCase()}</div>
            <div class="card-inner" id="card-${index}">
                <div class="card-front">
                    <h3>${card.question}</h3>
                </div>
                <div class="card-back">
                    <p>${card.answer}</p>
                </div>
            </div>
        </div>
    `).join('');
}

function flipCard(index) {
    const card = document.getElementById(`card-${index}`).parentElement;
    card.classList.toggle('flipped');
    
    // Track study progress
    if (!card.classList.contains('studied')) {
        card.classList.add('studied');
        appState.studyData.progress.cardsStudied++;
        updateProgressDisplay();
        addActivity(`Studied flashcard: "${appState.studyData.flashcards[index].question}"`, 'study');
    }
}

function shuffleCards() {
    const flashcards = appState.studyData.flashcards;
    for (let i = flashcards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [flashcards[i], flashcards[j]] = [flashcards[j], flashcards[i]];
    }
    renderFlashcards();
    showNotification('Flashcards shuffled! 🔀');
}

// Study Session Management
function toggleStudySession() {
    const btn = document.getElementById('sessionBtn');
    
    if (appState.session.isActive) {
        stopStudySession();
        btn.innerHTML = '▶️ Start Session';
    } else {
        startStudySession();
        btn.innerHTML = '⏸️ End Session';
    }
}

function startStudySession() {
    appState.session.isActive = true;
    appState.session.startTime = Date.now();
    appState.session.timer = setInterval(updateSessionTimer, 1000);
    
    addActivity('Started study session', 'session');
    showNotification('Study session started! 📚');
}

function stopStudySession() {
    if (appState.session.timer) {
        clearInterval(appState.session.timer);
    }
    
    const sessionDuration = Date.now() - appState.session.startTime;
    appState.studyData.progress.studyTime += Math.floor(sessionDuration / 60000); // Convert to minutes
    
    appState.session.isActive = false;
    appState.session.startTime = null;
    appState.session.timer = null;
    
    addActivity(`Completed study session (${formatTime(sessionDuration)})`, 'session');
    showNotification('Study session completed! 🎉');
    updateProgressDisplay();
}

function updateSessionTimer() {
    if (!appState.session.isActive || !appState.session.startTime) return;
    
    const elapsed = Date.now() - appState.session.startTime;
    const timer = document.getElementById('sessionTimer');
    
    if (timer) {
        timer.textContent = formatTime(elapsed);
    }
}

function formatTime(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
    } else {
        return `${minutes.toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
}

// Quiz Management
function renderQuiz() {
    const container = document.getElementById('quizContainer');
    const questions = appState.studyData.quizQuestions;
    
    if (questions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🧩</div>
                <h3>No Quiz Questions Yet</h3>
                <p>Generate some study materials first to start practicing!</p>
            </div>
        `;
        document.getElementById('startQuizBtn').style.display = 'none';
        return;
    }
    
    container.innerHTML = questions.map((q, qIndex) => `
        <div class="question-item" data-question-id="${q.id}">
            <div class="question">${q.question}</div>
            <div class="options">
                ${q.options.map((option, optIndex) => `
                    <div class="option" onclick="selectOption(${qIndex}, ${optIndex})" data-option="${optIndex}">
                        ${String.fromCharCode(65 + optIndex)}. ${option}
                    </div>
                `).join('')}
            </div>
            <button class="check-answer-btn" onclick="checkAnswer(${qIndex})" disabled>
                Check Answer
            </button>
            <div class="answer-feedback" id="feedback-${qIndex}" style="display: none; margin-top: 15px; padding: 15px; border-radius: 8px;"></div>
        </div>
    `).join('');
    
    document.getElementById('startQuizBtn').style.display = 'inline-block';
    document.getElementById('totalQuestions').textContent = questions.length;
}

function selectOption(questionIndex, optionIndex) {
    const questionItem = document.querySelectorAll('.question-item')[questionIndex];
    const options = questionItem.querySelectorAll('.option');
    
    // Clear previous selections
    options.forEach(opt => opt.classList.remove('selected'));
    
    // Select current option
    options[optionIndex].classList.add('selected');
    
    // Enable check answer button
    const checkBtn = questionItem.querySelector('.check-answer-btn');
    checkBtn.disabled = false;
}

function checkAnswer(questionIndex) {
    const question = appState.studyData.quizQuestions[questionIndex];
    const questionItem = document.querySelectorAll('.question-item')[questionIndex];
    const options = questionItem.querySelectorAll('.option');
    const selectedOption = questionItem.querySelector('.option.selected');
    const feedback = document.getElementById(`feedback-${questionIndex}`);
    const checkBtn = questionItem.querySelector('.check-answer-btn');
    
    if (!selectedOption) return;
    
    const selectedIndex = parseInt(selectedOption.dataset.option);
    const isCorrect = selectedIndex === question.correctAnswer;
    
    // Update answer tracking
    appState.studyData.progress.totalQuestions++;
    if (isCorrect) {
        appState.studyData.progress.correctAnswers++;
        appState.studyData.progress.streak++;
    } else {
        appState.studyData.progress.streak = 0;
    }
    
    // Visual feedback
    options.forEach((opt, index) => {
        if (index === question.correctAnswer) {
            opt.classList.add('correct');
        } else if (opt.classList.contains('selected') && index !== question.correctAnswer) {
            opt.classList.add('incorrect');
        }
        opt.onclick = null; // Disable further clicks
    });
    
    // Show feedback
    feedback.style.display = 'block';
    feedback.className = `answer-feedback ${isCorrect ? 'correct' : 'incorrect'}`;
    feedback.style.background = isCorrect ? 
        'linear-gradient(45deg, rgba(72, 187, 120, 0.1), rgba(56, 161, 105, 0.1))' :
        'linear-gradient(45deg, rgba(245, 101, 101, 0.1), rgba(229, 62, 62, 0.1))';
    feedback.style.border = `2px solid ${isCorrect ? '#48bb78' : '#f56565'}`;
    feedback.innerHTML = `
        <strong>${isCorrect ? '✅ Correct!' : '❌ Incorrect'}</strong><br>
        ${isCorrect ? 'Great job!' : `The correct answer is: ${question.options[question.correctAnswer]}`}
    `;
    
    checkBtn.style.display = 'none';
    
    // Update displays
    updateQuizScore();
    updateProgressDisplay();
    addActivity(`${isCorrect ? 'Answered correctly' : 'Answered incorrectly'}: "${question.question}"`, 'quiz');
    
    if (isCorrect && appState.studyData.progress.streak % 5 === 0) {
        showAchievement(`${appState.studyData.progress.streak} question streak! 🔥`);
    }
}

function updateQuizScore() {
    const score = appState.studyData.progress.totalQuestions > 0 ? 
        Math.round((appState.studyData.progress.correctAnswers / appState.studyData.progress.totalQuestions) * 100) : 0;
    
    document.getElementById('currentScore').textContent = appState.studyData.progress.correctAnswers;
    document.getElementById('quizScore').textContent = score + '%';
}

function startQuiz() {
    // Reset all question states
    renderQuiz();
    showNotification('Quiz started! Good luck! 🍀');
    addActivity('Started practice quiz', 'quiz');
}

function resetQuiz() {
    renderQuiz();
    showNotification('Quiz reset! 🔄');
}

// Progress Management
function updateProgressDisplay() {
    const progress = appState.studyData.progress;
    
    // Update stat cards
    document.getElementById('totalCards').textContent = progress.totalCards;
    document.getElementById('cardsStudied').textContent = progress.cardsStudied;
    document.getElementById('studyStreak').textContent = progress.streak;
    document.getElementById('studyTime').textContent = progress.studyTime + 'm';
    document.getElementById('topicsStudied').textContent = progress.topicsStudied;
    document.getElementById('streakCount').textContent = progress.streak;
    
    // Update progress bar
    const progressPercentage = progress.totalCards > 0 ? 
        Math.round((progress.cardsStudied / progress.totalCards) * 100) : 0;
    
    document.getElementById('overallProgress').style.width = progressPercentage + '%';
    document.getElementById('progressText').textContent = 
        progressPercentage === 100 ? 'All cards studied! 🎉' :
        progressPercentage > 0 ? `${progressPercentage}% completed - keep it up! 💪` :
        'Get started by generating your first study materials!';
    
    updateQuizScore();
}

// Activity Tracking
function addActivity(description, type) {
    const activity = {
        id: Date.now(),
        description,
        type,
        timestamp: new Date(),
        icon: getActivityIcon(type)
    };
    
    appState.studyData.recentActivity.unshift(activity);
    
    // Keep only last 10 activities
    if (appState.studyData.recentActivity.length > 10) {
        appState.studyData.recentActivity = appState.studyData.recentActivity.slice(0, 10);
    }
    
    updateActivityDisplay();
    saveUserData();
}

function getActivityIcon(type) {
    const icons = {
        'generate': '✨',
        'study': '📖',
        'quiz': '🧩',
        'session': '⏱️',
        'achievement': '🏆'
    };
    return icons[type] || '📝';
}

function updateActivityDisplay() {
    const container = document.getElementById('recentActivity');
    if (!container) return;
    
    const activities = appState.studyData.recentActivity;
    
    container.innerHTML = activities.length > 0 ? 
        activities.map(activity => `
            <div class="activity-item">
                <span class="activity-icon">${activity.icon}</span>
                <span>${activity.description}</span>
                <span class="activity-time">${formatTimeAgo(activity.timestamp)}</span>
            </div>
        `).join('') :
        '<div class="activity-item"><span class="activity-icon">🎯</span><span>No recent activity</span></div>';
}

function formatTimeAgo(timestamp) {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
}

// Analytics (Premium Feature)
function loadAnalytics() {
    if (!isPremiumUser()) {
        showPremiumUpsell('analytics');
        return;
    }
    
    // Load advanced analytics data
    renderPerformanceCharts();
    renderSubjectBreakdown();
    renderStudyPatterns();
}

function isPremiumUser() {
    return appState.user?.subscription === 'premium' || appState.user?.subscription === 'pro';
}

function showPremiumUpsell(feature) {
    showNotification(`${feature} is a premium feature. Upgrade to unlock! 👑`, 'info');
}

// Pricing and Payments
function updatePricingDisplay() {
    const currentPlan = appState.user?.subscription || 'free';
    
    // Update current plan button
    document.querySelectorAll('.pricing-card .auth-btn').forEach((btn, index) => {
        const plans = ['free', 'premium', 'pro'];
        if (plans[index] === currentPlan) {
            btn.textContent = '✓ Current Plan';
            btn.style.background = '#48bb78';
        }
    });
}

function selectPlan(planType) {
    if (planType === 'free') {
        showNotification('You are already on the free plan!', 'info');
        return;
    }
    
    if (appState.user?.subscription === planType) {
        showNotification(`You are already subscribed to ${planType}!`, 'info');
        return;
    }
    
    showPaymentModal(planType);
}

function showPaymentModal(planType) {
    const modal = document.getElementById('paymentModal');
    modal.style.display = 'flex';
    
    // Update payment summary based on plan
    const prices = { premium: '$9.99', pro: '$19.99' };
    const summary = modal.querySelector('.payment-summary');
    summary.innerHTML = `
        <p><strong>BrainyPal ${planType.charAt(0).toUpperCase() + planType.slice(1)} - ${prices[planType]}/month</strong></p>
        <p>✨ Unlimited AI generations</p>
        <p>📊 Advanced analytics</p>
        <p>📱 Mobile app access</p>
        ${planType === 'pro' ? '<p>🤖 AI tutor chat</p>' : ''}
    `;
}

function closePaymentModal() {
    document.getElementById('paymentModal').style.display = 'none';
}

async function processPayment() {
    // In a real app, this would integrate with Stripe
    showNotification('Processing payment...', 'info');
    
    // Simulate payment processing
    setTimeout(() => {
        appState.user.subscription = 'premium';
        updateUserInterface();
        closePaymentModal();
        showAchievement('Welcome to BrainyPal Premium! 🎉');
        addActivity('Upgraded to Premium', 'achievement');
        saveUserData();
    }, 2000);
}

// User Interface Updates
function updateUserInterface() {
    if (!appState.user) return;
    
    // Update user info in header
    document.getElementById('userName').textContent = appState.user.name;
    document.getElementById('userEmail').textContent = appState.user.email;
    document.getElementById('userAvatar').textContent = appState.user.name.split(' ').map(n => n[0]).join('').toUpperCase();
    
    // Update subscription status
    const statusEl = document.getElementById('subscriptionStatus');
    const subscription = appState.user.subscription || 'free';
    statusEl.textContent = subscription.toUpperCase() + ' PLAN';
    statusEl.className = `subscription-status ${subscription === 'free' ? '' : 'premium'}`;
    
    // Update usage limits
    updateUsageLimits();
}

function updateUsageLimits() {
    const userPlan = appState.user?.subscription || 'free';
    const limit = appState.limits[userPlan].dailyGenerations;
    
    if (limit !== -1 && appState.usage.today >= limit) {
        showUsageLimit();
    } else {
        hideUsageLimit();
    }
}

// Data Persistence
function saveUserData() {
    localStorage.setItem('brainypal_study_data', JSON.stringify(appState.studyData));
    localStorage.setItem('brainypal_user', JSON.stringify(appState.user));
}

function loadUserData() {
    try {
        const savedData = localStorage.getItem('brainypal_study_data');
        const savedUsage = localStorage.getItem('brainypal_usage');
        
        if (savedData) {
            appState.studyData = { ...appState.studyData, ...JSON.parse(savedData) };
        }
        
        if (savedUsage) {
            appState.usage = { ...appState.usage, ...JSON.parse(savedUsage) };
        }
        
        updateProgressDisplay();
        updateActivityDisplay();
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Sample Data for Demo
function loadSampleData() {
    if (appState.studyData.flashcards.length === 0) {
        const sampleFlashcards = [
            {
                id: Date.now(),
                question: "What is photosynthesis?",
                answer: "The process by which plants use sunlight to produce glucose from carbon dioxide and water",
                difficulty: "intermediate",
                topic: "Biology",
                created: new Date()
            },
            {
                id: Date.now() + 1,
                question: "What are the main components needed for photosynthesis?",
                answer: "Sunlight, carbon dioxide, water, and chlorophyll",
                difficulty: "beginner",
                topic: "Biology",
                created: new Date()
            }
        ];
        
        const sampleQuestions = [
            {
                id: Date.now(),
                question: "What is the primary purpose of photosynthesis?",
                options: ["To produce oxygen", "To produce glucose for energy", "To absorb carbon dioxide", "To create water"],
                correctAnswer: 1,
                topic: "Biology",
                difficulty: "intermediate"
            }
        ];
        
        appState.studyData.flashcards = sampleFlashcards;
        appState.studyData.quizQuestions = sampleQuestions;
        appState.studyData.progress.totalCards = sampleFlashcards.length;
        appState.studyData.progress.topicsStudied = 1;
        
        addActivity('Sample study materials loaded', 'generate');
        saveUserData();
    }
}

// Floating Particles Animation
function createFloatingParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        container.appendChild(particle);
    }
}

// Notification System
function showNotification(message, type = 'success') {
    const toast = document.getElementById('notificationToast');
    const colors = {
        success: '#48bb78',
        error: '#f56565',
        info: '#4299e1'
    };
    
    toast.style.background = colors[type] || colors.success;
    document.getElementById('notificationText').textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showAchievement(text) {
    const popup = document.getElementById('achievementPopup');
    document.getElementById('achievementText').textContent = text;
    popup.classList.add('show');
    
    setTimeout(() => {
        popup.classList.remove('show');
    }, 4000);
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Error Handling
window.addEventListener('error', function(event) {
    console.error('Application error:', event.error);
    showNotification('Something went wrong. Please refresh the page.', 'error');
});

// Auto-save functionality
setInterval(() => {
    if (appState.user) {
        saveUserData();
    }
}, 30000); // Save every 30 seconds

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to generate materials
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (appState.currentTab === 'generate') {
                generateStudyMaterials();
            }
        }
        
        // Space to flip current flashcard
        if (e.code === 'Space' && appState.currentTab === 'flashcards') {
            e.preventDefault();
            const firstCard = document.querySelector('.flashcard:not(.flipped)');
            if (firstCard) {
                firstCard.click();
            }
        }
    });
    
    // Auto-resize textareas
    document.addEventListener('input', function(e) {
        if (e.target.tagName === 'TEXTAREA') {
            e.target.style.height = 'auto';
            e.target.style.height = (e.target.scrollHeight) + 'px';
        }
    });
});

// Export functions for use in other files
window.BrainyPal = {
    switchTab,
    generateStudyMaterials,
    flipCard,
    selectOption,
    checkAnswer,
    toggleStudySession,
    shuffleCards,
    selectPlan,
    showNotification,
    updateProgressDisplay
};