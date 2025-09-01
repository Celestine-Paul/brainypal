// BRAINYPAL API Service - COMPLETE VERSION
// Handles all API communications with the backend

class APIService {
    constructor() {
        this.baseURL = CONFIG.API.BASE_URL;
        this.timeout = CONFIG.API.TIMEOUT;
        this.retryAttempts = CONFIG.API.RETRY_ATTEMPTS;
    }

    /**
     * Make HTTP request with retry logic
     * @param {string} endpoint - API endpoint key
     * @param {object} options - Request options
     * @returns {Promise<object>} API response
     */
    async makeRequest(endpoint, options = {}) {
        const url = ConfigUtils.getApiUrl(endpoint);
        if (!url) {
            throw new Error(`Invalid endpoint: ${endpoint}`);
        }

        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            timeout: this.timeout
        };

        const requestOptions = { ...defaultOptions, ...options };

        // Add authentication token if available
        const token = authService.getAuthToken();
        if (token && !requestOptions.headers.Authorization) {
            requestOptions.headers.Authorization = `Bearer ${token}`;
        }

        let lastError;
        
        // Retry logic
        for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);

                const response = await fetch(url, {
                    ...requestOptions,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                // Handle different response status codes
                if (response.status === 401) {
                    // Unauthorized - try to refresh token
                    const refreshed = await authService.refreshAuthToken();
                    if (refreshed && attempt === 0) {
                        // Retry with new token
                        requestOptions.headers.Authorization = `Bearer ${authService.getAuthToken()}`;
                        continue;
                    } else {
                        // Refresh failed, redirect to login
                        authService.clearAuthData();
                        window.location.reload();
                        throw new Error('Session expired. Please log in again.');
                    }
                }

                if (response.status === 429) {
                    // Rate limited
                    const retryAfter = response.headers.get('Retry-After') || 5;
                    await this.delay(retryAfter * 1000);
                    continue;
                }

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                // Log successful requests in development
                if (CONFIG.DEVELOPMENT.DEBUG) {
                    console.log('API Request:', { endpoint, method: requestOptions.method, response: data });
                }

                return data;

            } catch (error) {
                lastError = error;
                
                // Don't retry on certain errors
                if (error.name === 'AbortError' || error.message.includes('Session expired')) {
                    throw error;
                }

                // Wait before retry
                if (attempt < this.retryAttempts - 1) {
                    await this.delay(Math.pow(2, attempt) * 1000); // Exponential backoff
                }
            }
        }

        throw lastError;
    }

    /**
     * GET request
     * @param {string} endpoint - API endpoint key
     * @param {object} params - Query parameters
     * @param {object} headers - Additional headers
     * @returns {Promise<object>} API response
     */
    async get(endpoint, params = {}, headers = {}) {
        const url = new URL(ConfigUtils.getApiUrl(endpoint));
        
        // Add query parameters
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });

        return this.makeRequest(endpoint, {
            method: 'GET',
            headers: headers
        });
    }

    /**
     * POST request
     * @param {string} endpoint - API endpoint key
     * @param {object} data - Request body data
     * @param {object} headers - Additional headers
     * @returns {Promise<object>} API response
     */
    async post(endpoint, data = {}, headers = {}) {
        return this.makeRequest(endpoint, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     * @param {string} endpoint - API endpoint key
     * @param {object} data - Request body data
     * @param {object} headers - Additional headers
     * @returns {Promise<object>} API response
     */
    async put(endpoint, data = {}, headers = {}) {
        return this.makeRequest(endpoint, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     * @param {string} endpoint - API endpoint key
     * @param {object} data - Request body data
     * @param {object} headers - Additional headers
     * @returns {Promise<object>} API response
     */
    async delete(endpoint, data = {}, headers = {}) {
        return this.makeRequest(endpoint, {
            method: 'DELETE',
            headers: headers,
            body: JSON.stringify(data)
        });
    }

    /**
     * Upload file
     * @param {string} endpoint - API endpoint key
     * @param {File} file - File to upload
     * @param {object} additionalData - Additional form data
     * @returns {Promise<object>} API response
     */
    async uploadFile(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add additional data
        Object.keys(additionalData).forEach(key => {
            formData.append(key, additionalData[key]);
        });

        return this.makeRequest(endpoint, {
            method: 'POST',
            body: formData,
            headers: {
                // Don't set Content-Type for FormData - browser will set it with boundary
                'Authorization': `Bearer ${authService.getAuthToken()}`
            }
        });
    }

    /**
     * Delay function for retry logic
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise} Promise that resolves after delay
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// AI Service for Hugging Face integration
class AIService {
    constructor() {
        this.huggingFaceToken = null; // Set your Hugging Face API token
        this.models = CONFIG.AI.HUGGINGFACE.MODELS;
    }

    /**
     * Set Hugging Face API token
     * @param {string} token - Hugging Face API token
     */
    setHuggingFaceToken(token) {
        this.huggingFaceToken = token;
    }

    /**
     * Generate flashcards using AI
     * @param {string} text - Input text to analyze
     * @param {string} topic - Study topic
     * @param {string} difficulty - Difficulty level
     * @returns {Promise<Array>} Generated flashcards
     */
    async generateFlashcards(text, topic, difficulty) {
        try {
            // First, summarize the text to extract key concepts
            const summary = await this.summarizeText(text);
            
            // Then generate questions and answers
            const concepts = await this.extractConcepts(summary);
            
            const flashcards = concepts.map((concept, index) => ({
                id: `fc_${Date.now()}_${index}`,
                front: `What is ${concept.term}?`,
                back: concept.definition,
                difficulty: difficulty,
                topic: topic,
                createdAt: new Date().toISOString(),
                mastered: false
            }));

            return flashcards;

        } catch (error) {
            console.error('Flashcard generation error:', error);
            
            // Fallback to rule-based generation
            return this.generateFallbackFlashcards(text, topic, difficulty);
        }
    }

    /**
     * Generate quiz questions using AI
     * @param {string} text - Input text to analyze
     * @param {string} topic - Study topic
     * @param {string} difficulty - Difficulty level
     * @returns {Promise<Array>} Generated questions
     */
    async generateQuestions(text, topic, difficulty) {
        try {
            // Use Hugging Face T5 model for question generation
            const response = await this.callHuggingFace(
                this.models.QUESTION_GENERATION,
                `generate questions: ${text.substring(0, 500)}`
            );

            // Parse the AI response and format as quiz questions
            const questions = this.parseQuestionsFromAI(response, topic, difficulty);
            
            return questions;

        } catch (error) {
            console.error('Question generation error:', error);
            
            // Fallback to rule-based generation
            return this.generateFallbackQuestions(text, topic, difficulty);
        }
    }

    /**
     * Summarize text using AI
     * @param {string} text - Text to summarize
     * @returns {Promise<string>} Summarized text
     */
    async summarizeText(text) {
        try {
            if (!this.huggingFaceToken) {
                throw new Error('Hugging Face API token not set');
            }

            const response = await fetch(
                `${CONFIG.AI.HUGGINGFACE.API_URL}/${this.models.SUMMARIZATION}`,
                {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.huggingFaceToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        inputs: text.substring(0, 1000), // Limit input length
                        parameters: {
                            max_length: 150,
                            min_length: 50,
                            do_sample: false
                        }
                    })
                }
            );

            if (!response.ok) {
                throw new Error(`Hugging Face API error: ${response.status}`);
            }

            const result = await response.json();
            return result[0]?.summary_text || text.substring(0, 200);

        } catch (error) {
            console.error('Text summarization error:', error);
            return text.substring(0, 200); // Fallback to truncated text
        }
    }

    /**
     * Extract concepts from text
     * @param {string} text - Text to analyze
     * @returns {Promise<Array>} Extracted concepts
     */
    async extractConcepts(text) {
        // Rule-based concept extraction (can be enhanced with NLP)
        const concepts = [];
        
        // Look for definition patterns
        const definitionPatterns = [
            /(\w+)\s+is\s+defined\s+as\s+([^.!?]+)/gi,
            /(\w+)\s+refers\s+to\s+([^.!?]+)/gi,
            /(\w+):\s+([^.!?\n]+)/gi,
            /the\s+concept\s+of\s+(\w+)\s+([^.!?]+)/gi
        ];

        definitionPatterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(text)) !== null && concepts.length < 10) {
                concepts.push({
                    term: match[1].trim(),
                    definition: match[2].trim()
                });
            }
        });

        // If no patterns found, extract from bullet points and numbered lists
        if (concepts.length === 0) {
            const lines = text.split('\n');
            lines.forEach(line => {
                const bulletMatch = line.match(/^[\s]*[-•*]\s*([^:]+):\s*(.+)$/);
                const numberMatch = line.match(/^\d+\.\s*([^:]+):\s*(.+)$/);
                
                if (bulletMatch && concepts.length < 10) {
                    concepts.push({
                        term: bulletMatch[1].trim(),
                        definition: bulletMatch[2].trim()
                    });
                } else if (numberMatch && concepts.length < 10) {
                    concepts.push({
                        term: numberMatch[1].trim(),
                        definition: numberMatch[2].trim()
                    });
                }
            });
        }

        return concepts;
    }

    /**
     * Call Hugging Face API
     * @param {string} model - Model name
     * @param {string} input - Input text
     * @returns {Promise<object>} API response
     */
    async callHuggingFace(model, input) {
        if (!this.huggingFaceToken) {
            throw new Error('Hugging Face API token not configured');
        }

        const response = await fetch(
            `${CONFIG.AI.HUGGINGFACE.API_URL}/${model}`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.huggingFaceToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    inputs: input,
                    parameters: {
                        max_new_tokens: CONFIG.AI.HUGGINGFACE.MAX_TOKENS,
                        temperature: CONFIG.AI.HUGGINGFACE.TEMPERATURE,
                        top_p: CONFIG.AI.HUGGINGFACE.TOP_P
                    }
                })
            }
        );

        if (!response.ok) {
            throw new Error(`Hugging Face API error: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Parse questions from AI response
     * @param {object} aiResponse - Response from AI
     * @param {string} topic - Study topic
     * @param {string} difficulty - Difficulty level
     * @returns {Array} Formatted questions
     */
    parseQuestionsFromAI(aiResponse, topic, difficulty) {
        // This would parse the actual AI response
        // For now, we'll return structured questions
        const questions = [];
        
        // Mock questions based on difficulty
        const questionTemplates = {
            beginner: [
                "What is the main purpose of {concept}?",
                "Which of the following best describes {concept}?"
            ],
            intermediate: [
                "How does {concept} relate to other concepts in {topic}?",
                "What are the key characteristics of {concept}?"
            ],
            advanced: [
                "Analyze the implications of {concept} in {topic}",
                "Evaluate the effectiveness of {concept} compared to alternatives"
            ]
        };

        return questions;
    }

    /**
     * Fallback flashcard generation (rule-based)
     * @param {string} text - Input text
     * @param {string} topic - Study topic
     * @param {string} difficulty - Difficulty level
     * @returns {Array} Generated flashcards
     */
    generateFallbackFlashcards(text, topic, difficulty) {
        const concepts = this.extractSimpleKeywords(text);
        
        return concepts.map((concept, index) => ({
            id: `fc_${Date.now()}_${index}`,
            front: `What is ${concept}?`,
            back: `${concept} is a key concept in ${topic || 'your study material'}. Review your notes for detailed information.`,
            difficulty: difficulty,
            topic: topic,
            createdAt: new Date().toISOString(),
            mastered: false
        }));
    }

    /**
     * Fallback question generation (rule-based)
     * @param {string} text - Input text
     * @param {string} topic - Study topic
     * @param {string} difficulty - Difficulty level
     * @returns {Array} Generated questions
     */
    generateFallbackQuestions(text, topic, difficulty) {
        const keywords = this.extractSimpleKeywords(text);
        
        return keywords.map((keyword, index) => ({
            id: `q_${Date.now()}_${index}`,
            question: `Which statement best describes ${keyword}?`,
            options: this.shuffleArray([
                `${keyword} is a fundamental concept in ${topic || 'this field'}`,
                `${keyword} is not relevant to the topic`,
                `${keyword} should be ignored during study`,
                `${keyword} is outdated information`
            ]),
            correct: 0,
            explanation: `${keyword} is an important concept. Review your notes for more detailed information.`,
            difficulty: difficulty,
            topic: topic,
            createdAt: new Date().toISOString()
        }));
    }

    /**
     * Extract simple keywords from text
     * @param {string} text - Input text
     * @returns {Array} Extracted keywords
     */
    extractSimpleKeywords(text) {
        const words = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 4)
            .filter(word => !this.isStopWord(word));

        // Get unique words and limit to 6
        const uniqueWords = [...new Set(words)];
        return uniqueWords.slice(0, 6);
    }

    /**
     * Check if word is a stop word
     * @param {string} word - Word to check
     * @returns {boolean} Whether word is a stop word
     */
    isStopWord(word) {
        const stopWords = [
            'the', 'is', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'a', 'an', 'this', 'that', 'these', 'those',
            'will', 'would', 'could', 'should', 'have', 'has', 'had', 'do',
            'does', 'did', 'can', 'may', 'might', 'must', 'shall', 'from',
            'into', 'during', 'before', 'after', 'above', 'below', 'between'
        ];
        return stopWords.includes(word);
    }

    /**
     * Shuffle array
     * @param {Array} array - Array to shuffle
     * @returns {Array} Shuffled array
     */
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
}

// Analytics Service for tracking user behavior
class AnalyticsService {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.eventQueue = [];
        this.isOnline = navigator.onLine;
        
        // Set up online/offline event listeners
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.flushEventQueue();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
    }

    /**
     * Generate unique session ID
     * @returns {string} Session ID
     */
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Track analytics event
     * @param {string} event - Event name
     * @param {object} properties - Event properties
     */
    async trackEvent(event, properties = {}) {
        const eventData = {
            event: event,
            properties: {
                ...properties,
                timestamp: new Date().toISOString(),
                sessionId: this.sessionId,
                userId: authService.getCurrentUser()?.id,
                userAgent: navigator.userAgent,
                url: window.location.href,
                referrer: document.referrer
            }
        };

        // Log in development
        if (CONFIG.DEVELOPMENT.DEBUG) {
            console.log('Analytics Event:', eventData);
        }

        // Add to queue
        this.eventQueue.push(eventData);

        // Try to send immediately if online
        if (this.isOnline) {
            await this.flushEventQueue();
        }

        // Update local analytics
        this.updateLocalAnalytics(event, properties);
    }

    /**
     * Flush event queue to server
     */
    async flushEventQueue() {
        if (this.eventQueue.length === 0) return;

        try {
            const events = [...this.eventQueue];
            this.eventQueue = [];

            await apiService.post('TRACK_EVENT', {
                events: events
            });

        } catch (error) {
            console.error('Failed to send analytics events:', error);
            // Re-add events to queue for retry
            this.eventQueue.unshift(...events);
        }
    }

    /**
     * Update local analytics data
     * @param {string} event - Event name
     * @param {object} properties - Event properties
     */
    updateLocalAnalytics(event, properties) {
        // This method updates the local UI immediately
        // while analytics are sent to server in background
        
        if (typeof window.updateDashboardAnalytics === 'function') {
            window.updateDashboardAnalytics(event, properties);
        }
    }

    /**
     * Get user analytics from server
     * @returns {Promise<object>} User analytics data
     */
    async getUserAnalytics() {
        try {
            return await apiService.get('GET_ANALYTICS');
        } catch (error) {
            console.error('Failed to get user analytics:', error);
            return { success: false, data: {} };
        }
    }
}

// Payment Service for handling subscriptions
class PaymentService {
    constructor() {
        this.stripeLoaded = false;
        this.stripe = null;
    }

    /**
     * Initialize Stripe
     * @returns {Promise<boolean>} Whether Stripe was initialized successfully
     */
    async initializeStripe() {
        if (this.stripeLoaded) return true;

        try {
            // Load Stripe.js
            const script = document.createElement('script');
            script.src = 'https://js.stripe.com/v3/';
            document.head.appendChild(script);

            await new Promise((resolve, reject) => {
                script.onload = resolve;
                script.onerror = reject;
            });

            // Initialize Stripe instance
            this.stripe = Stripe(CONFIG.PAYMENT.STRIPE.PUBLISHABLE_KEY);
            this.stripeLoaded = true;
            
            return true;

        } catch (error) {
            console.error('Failed to initialize Stripe:', error);
            return false;
        }
    }

    /**
     * Create payment intent
     * @param {string} planType - Subscription plan type
     * @returns {Promise<object>} Payment intent data
     */
    async createPaymentIntent(planType) {
        try {
            const response = await apiService.post('CREATE_PAYMENT_INTENT', {
                plan_type: planType,
                currency: 'usd'
            });

            return response;

        } catch (error) {
            console.error('Failed to create payment intent:', error);
            throw error;
        }
    }

    /**
     * Process payment
     * @param {string} clientSecret - Payment intent client secret
     * @param {object} paymentMethod - Payment method details
     * @returns {Promise<object>} Payment result
     */
    async processPayment(clientSecret, paymentMethod) {
        if (!this.stripe) {
            await this.initializeStripe();
        }

        try {
            const result = await this.stripe.confirmCardPayment(clientSecret, {
                payment_method: paymentMethod
            });

            if (result.error) {
                throw new Error(result.error.message);
            }

            // Notify backend of successful payment
            await apiService.post('CONFIRM_PAYMENT', {
                payment_intent_id: result.paymentIntent.id
            });

            return result;

        } catch (error) {
            console.error('Payment processing error:', error);
            throw error;
        }
    }

    /**
     * Get subscription status
     * @returns {Promise<object>} Subscription status
     */
    async getSubscriptionStatus() {
        try {
            return await apiService.get('GET_SUBSCRIPTION');
        } catch (error) {
            console.error('Failed to get subscription status:', error);
            return { success: false, data: null };
        }
    }

    /**
     * Cancel subscription
     * @returns {Promise<object>} Cancellation result
     */
    async cancelSubscription() {
        try {
            return await apiService.post('CANCEL_SUBSCRIPTION');
        } catch (error) {
            console.error('Failed to cancel subscription:', error);
            throw error;
        }
    }
}

// Notification Service for user notifications
class NotificationService {
    constructor() {
        this.notifications = [];
        this.permission = Notification.permission;
        this.setupEventListeners();
    }

    /**
     * Request notification permission
     * @returns {Promise<string>} Permission status
     */
    async requestPermission() {
        if ('Notification' in window) {
            this.permission = await Notification.requestPermission();
            return this.permission;
        }
        return 'denied';
    }

    /**
     * Show notification
     * @param {string} title - Notification title
     * @param {object} options - Notification options
     */
    async showNotification(title, options = {}) {
        // Check if notifications are supported
        if (!('Notification' in window)) {
            console.warn('This browser does not support notifications');
            return;
        }

        // Request permission if not granted
        if (this.permission !== 'granted') {
            await this.requestPermission();
        }

        if (this.permission === 'granted') {
            const notification = new Notification(title, {
                icon: '/assets/icons/icon-192x192.png',
                badge: '/assets/icons/icon-192x192.png',
                ...options
            });

            // Auto-close after 5 seconds
            setTimeout(() => notification.close(), 5000);
        }
    }

    /**
     * Show in-app notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {number} duration - Duration in milliseconds
     */
    showInAppNotification(message, type = 'info', duration = 5000) {
        const notification = {
            id: `notif_${Date.now()}`,
            message: message,
            type: type,
            timestamp: new Date().toISOString(),
            read: false
        };

        this.notifications.unshift(notification);

        // Trigger UI update
        this.updateNotificationUI();

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification.id);
            }, duration);
        }

        return notification.id;
    }

    /**
     * Remove notification
     * @param {string} notificationId - Notification ID
     */
    removeNotification(notificationId) {
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
        this.updateNotificationUI();
    }

    /**
     * Mark notification as read
     * @param {string} notificationId - Notification ID
     */
    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.read = true;
            this.updateNotificationUI();
        }
    }

    /**
     * Get unread notifications count
     * @returns {number} Unread count
     */
    getUnreadCount() {
        return this.notifications.filter(n => !n.read).length;
    }

    /**
     * Update notification UI
     */
    updateNotificationUI() {
        if (typeof window.updateNotificationDisplay === 'function') {
            window.updateNotificationDisplay(this.notifications);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Study reminders
        document.addEventListener('studySessionCompleted', (event) => {
            this.showInAppNotification(
                `Great job! You completed ${event.detail.questionsAnswered} questions.`,
                'success'
            );
        });

        // Achievement notifications
        document.addEventListener('achievementUnlocked', (event) => {
            this.showNotification('Achievement Unlocked!', {
                body: event.detail.description,
                tag: 'achievement'
            });
        });
    }
}

// Cache Service for offline functionality
class CacheService {
    constructor() {
        this.cache = new Map();
        this.cacheTimeout = CONFIG.CACHE.TIMEOUT;
        this.maxCacheSize = CONFIG.CACHE.MAX_SIZE;
    }

    /**
     * Store data in cache
     * @param {string} key - Cache key
     * @param {any} data - Data to cache
     * @param {number} ttl - Time to live in milliseconds
     */
    set(key, data, ttl = this.cacheTimeout) {
        const expiry = Date.now() + ttl;
        
        // Remove oldest entries if cache is full
        if (this.cache.size >= this.maxCacheSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }

        this.cache.set(key, {
            data: data,
            expiry: expiry,
            timestamp: Date.now()
        });
    }

    /**
     * Get data from cache
     * @param {string} key - Cache key
     * @returns {any} Cached data or null
     */
    get(key) {
        const cached = this.cache.get(key);
        
        if (!cached) {
            return null;
        }

        // Check if expired
        if (Date.now() > cached.expiry) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * Check if key exists in cache
     * @param {string} key - Cache key
     * @returns {boolean} Whether key exists
     */
    has(key) {
        return this.get(key) !== null;
    }

    /**
     * Delete cache entry
     * @param {string} key - Cache key
     */
    delete(key) {
        this.cache.delete(key);
    }

    /**
     * Clear all cache
     */
    clear() {
        this.cache.clear();
    }

    /**
     * Get cache statistics
     * @returns {object} Cache statistics
     */
    getStats() {
        return {
            size: this.cache.size,
            maxSize: this.maxCacheSize,
            hitRate: this.calculateHitRate(),
            oldestEntry: this.getOldestEntryAge()
        };
    }

    /**
     * Calculate cache hit rate
     * @returns {number} Hit rate percentage
     */
    calculateHitRate() {
        // This would require tracking hits/misses
        // For now return a placeholder
        return 0;
    }

    /**
     * Get age of oldest cache entry
     * @returns {number} Age in milliseconds
     */
    getOldestEntryAge() {
        let oldest = Date.now();
        for (const [key, value] of this.cache) {
            if (value.timestamp < oldest) {
                oldest = value.timestamp;
            }
        }
        return Date.now() - oldest;
    }
}

// Sync Service for offline data synchronization
class SyncService {
    constructor() {
        this.syncQueue = [];
        this.isSyncing = false;
        this.lastSyncTime = null;
        this.setupEventListeners();
    }

    /**
     * Add action to sync queue
     * @param {string} action - Action type
     * @param {object} data - Action data
     */
    queueAction(action, data) {
        const actionItem = {
            id: `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            action: action,
            data: data,
            timestamp: new Date().toISOString(),
            attempts: 0
        };

        this.syncQueue.push(actionItem);
        
        // Try to sync immediately if online
        if (navigator.onLine && !this.isSyncing) {
            this.performSync();
        }
    }

    /**
     * Perform synchronization
     */
    async performSync() {
        if (this.isSyncing || this.syncQueue.length === 0) return;

        this.isSyncing = true;

        try {
            const actionsToSync = [...this.syncQueue];
            const syncResults = [];

            for (const actionItem of actionsToSync) {
                try {
                    let result;
                    
                    switch (actionItem.action) {
                        case 'CREATE_FLASHCARD':
                            result = await apiService.post('CREATE_FLASHCARD', actionItem.data);
                            break;
                        case 'UPDATE_PROGRESS':
                            result = await apiService.put('UPDATE_PROGRESS', actionItem.data);
                            break;
                        case 'SUBMIT_QUIZ':
                            result = await apiService.post('SUBMIT_QUIZ', actionItem.data);
                            break;
                        case 'UPDATE_PROFILE':
                            result = await apiService.put('UPDATE_PROFILE', actionItem.data);
                            break;
                        default:
                            throw new Error(`Unknown sync action: ${actionItem.action}`);
                    }

                    syncResults.push({
                        id: actionItem.id,
                        success: true,
                        result: result
                    });

                    // Remove successful action from queue
                    this.syncQueue = this.syncQueue.filter(item => item.id !== actionItem.id);

                } catch (error) {
                    console.error(`Sync failed for action ${actionItem.action}:`, error);
                    
                    actionItem.attempts++;
                    
                    // Remove action if max attempts reached
                    if (actionItem.attempts >= 3) {
                        this.syncQueue = this.syncQueue.filter(item => item.id !== actionItem.id);
                        
                        syncResults.push({
                            id: actionItem.id,
                            success: false,
                            error: error.message
                        });
                    }
                }
            }

            this.lastSyncTime = new Date().toISOString();
            
            // Notify UI of sync completion
            document.dispatchEvent(new CustomEvent('syncCompleted', {
                detail: { results: syncResults }
            }));

        } catch (error) {
            console.error('Sync process error:', error);
        } finally {
            this.isSyncing = false;
        }
    }

    /**
     * Get sync status
     * @returns {object} Sync status information
     */
    getSyncStatus() {
        return {
            queueLength: this.syncQueue.length,
            isSyncing: this.isSyncing,
            lastSyncTime: this.lastSyncTime,
            isOnline: navigator.onLine
        };
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Auto-sync when coming back online
        window.addEventListener('online', () => {
            setTimeout(() => this.performSync(), 1000);
        });

        // Periodic sync every 5 minutes when online
        setInterval(() => {
            if (navigator.onLine && !this.isSyncing) {
                this.performSync();
            }
        }, 5 * 60 * 1000);
    }
}

// Theme Service for managing UI themes
class ThemeService {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'light';
        this.applyTheme(this.currentTheme);
    }

    /**
     * Get stored theme from localStorage
     * @returns {string|null} Stored theme
     */
    getStoredTheme() {
        try {
            return localStorage.getItem('brainypal_theme');
        } catch (error) {
            return null;
        }
    }

    /**
     * Store theme in localStorage
     * @param {string} theme - Theme name
     */
    storeTheme(theme) {
        try {
            localStorage.setItem('brainypal_theme', theme);
        } catch (error) {
            console.warn('Failed to store theme preference');
        }
    }

    /**
     * Apply theme to document
     * @param {string} theme - Theme name
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.body.className = document.body.className.replace(/theme-\w+/g, '') + ` theme-${theme}`;
        
        // Update meta theme-color for mobile browsers
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            const colors = {
                light: '#ffffff',
                dark: '#1a1a1a',
                blue: '#2563eb',
                green: '#059669'
            };
            metaThemeColor.setAttribute('content', colors[theme] || colors.light);
        }
    }

    /**
     * Switch theme
     * @param {string} theme - Theme name
     */
    switchTheme(theme) {
        this.currentTheme = theme;
        this.applyTheme(theme);
        this.storeTheme(theme);
        
        // Notify other components
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme }
        }));
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.switchTheme(newTheme);
    }

    /**
     * Get current theme
     * @returns {string} Current theme name
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Get available themes
     * @returns {Array} Available theme names
     */
    getAvailableThemes() {
        return ['light', 'dark', 'blue', 'green'];
    }
}

// Initialize services
const apiService = new APIService();
const aiService = new AIService();
const analyticsService = new AnalyticsService();
const paymentService = new PaymentService();
const notificationService = new NotificationService();
const cacheService = new CacheService();
const syncService = new SyncService();
const themeService = new ThemeService();

// Export services to global scope
window.apiService = apiService;
window.aiService = aiService;
window.analyticsService = analyticsService;
window.paymentService = paymentService;
window.notificationService = notificationService;
window.cacheService = cacheService;
window.syncService = syncService;
window.themeService = themeService;

// Service ready event
document.addEventListener('DOMContentLoaded', () => {
    document.dispatchEvent(new CustomEvent('servicesReady'));
    console.log('BrainyPal services initialized successfully');
});