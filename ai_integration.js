// BrainyPal - AI Integration and Backend Communication
// ai-integration.js

// AI Configuration
const AI_CONFIG = {
    huggingFace: {
        apiKey: 'YOUR_HUGGING_FACE_API_KEY', // Replace with actual API key
        baseURL: 'https://api-inference.huggingface.co/models',
        models: {
            textGeneration: 'microsoft/DialoGPT-medium',
            questionGeneration: 'valhalla/t5-base-qg-hl',
            summarization: 'facebook/bart-large-cnn',
            textClassification: 'cardiffnlp/twitter-roberta-base-emotion'
        }
    },
    openAI: {
        apiKey: 'YOUR_OPENAI_API_KEY', // Alternative AI provider
        baseURL: 'https://api.openai.com/v1'
    }
};

// File processing utilities
class FileProcessor {
    static async processFile(file) {
        const fileType = file.type;
        
        try {
            if (fileType.includes('text')) {
                return await this.processTextFile(file);
            } else if (fileType.includes('pdf')) {
                return await this.processPDFFile(file);
            } else if (fileType.includes('word') || fileType.includes('document')) {
                return await this.processWordFile(file);
            } else {
                throw new Error('Unsupported file type');
            }
        } catch (error) {
            console.error('File processing error:', error);
            throw new Error(`Failed to process ${file.name}: ${error.message}`);
        }
    }
    
    static async processTextFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = e => resolve(e.target.result);
            reader.onerror = e => reject(new Error('Failed to read text file'));
            reader.readAsText(file);
        });
    }
    
    static async processPDFFile(file) {
        // In a real app, you would use PDF.js or send to backend for processing
        // For demo, simulate PDF text extraction
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(`Extracted text content from PDF: ${file.name}\n\nThis would contain the actual PDF text content in a real implementation.`);
            }, 1000);
        });
    }
    
    static async processWordFile(file) {
        // In a real app, you would use mammoth.js or send to backend
        // For demo, simulate Word document processing
        return new Promise(resolve => {
            setTimeout(() => {
                resolve(`Extracted text content from Word document: ${file.name}\n\nThis would contain the actual document text content in a real implementation.`);
            }, 1000);
        });
    }
}

// AI Content Generation
class AIContentGenerator {
    static async generateFlashcards(content, topic, settings) {
        try {
            // Try Hugging Face API first
            const response = await this.callHuggingFaceAPI(content, topic, settings, 'flashcards');
            return response;
        } catch (error) {
            console.error('AI API error, falling back to mock generation:', error);
            return this.generateMockFlashcards(content, topic, settings);
        }
    }
    
    static async generateQuestions(content, topic, settings) {
        try {
            // Try Hugging Face API first
            const response = await this.callHuggingFaceAPI(content, topic, settings, 'questions');
            return response;
        } catch (error) {
            console.error('AI API error, falling back to mock generation:', error);
            return this.generateMockQuestions(content, topic, settings);
        }
    }
    
    static async callHuggingFaceAPI(content, topic, settings, type) {
        const apiKey = AI_CONFIG.huggingFace.apiKey;
        
        if (!apiKey || apiKey === 'YOUR_HUGGING_FACE_API_KEY') {
            throw new Error('Hugging Face API key not configured');
        }
        
        const model = type === 'flashcards' ? 
            AI_CONFIG.huggingFace.models.textGeneration : 
            AI_CONFIG.huggingFace.models.questionGeneration;
        
        const prompt = this.buildPrompt(content, topic, settings, type);
        
        const response = await fetch(`${AI_CONFIG.huggingFace.baseURL}/${model}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                inputs: prompt,
                parameters: {
                    max_length: 500,
                    temperature: 0.7,
                    do_sample: true
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }
        
        const data = await response.json();
        return this.parseAIResponse(data, type, settings);
    }
    
    static buildPrompt(content, topic, settings, type) {
        const basePrompt = `Topic: ${topic}\nContent: ${content}\n\n`;
        
        if (type === 'flashcards') {
            return `${basePrompt}Generate ${settings.cardCount} flashcards for studying ${topic}. 
                    Each flashcard should have a clear question and a comprehensive answer.
                    Difficulty level: ${settings.difficulty}
                    Focus on: ${settings.contentType}
                    
                    Format each flashcard as:
                    Q: [Question]
                    A: [Answer a,b,c,d]
                    A: [Correct answer]
                    ---`;
        } else {
            return `${basePrompt}Generate ${settings.questionCount} multiple choice questions about ${topic}.
                    Each question should have 4 options with one correct answer.
                    Difficulty level: ${settings.difficulty}
                    
                    Format each question as:
                    Q: [Question]
                    A) [Option 1]
                    B) [Option 2]  
                    C) [Option 3]
                    D) [Option 4]
                    Correct: [A/B/C/D]
                    ---`;
        }
    }
    
    static parseAIResponse(apiResponse, type, settings) {
        // Parse the AI response and format it properly
        // This is a simplified parser - in production, you'd need more robust parsing
        
        if (type === 'flashcards') {
            return this.parseFlashcardsResponse(apiResponse, settings);
        } else {
            return this.parseQuestionsResponse(apiResponse, settings);
        }
    }
    
    static parseFlashcardsResponse(response, settings) {
        // Mock parsing for demo - replace with actual AI response parsing
        const flashcards = [];
        for (let i = 0; i < settings.cardCount; i++) {
            flashcards.push({
                id: Date.now() + i,
                question: `AI-generated question ${i + 1} about the topic`,
                answer: `AI-generated comprehensive answer for question ${i + 1}`,
                difficulty: settings.difficulty,
                topic: settings.topic || 'Study Topic',
                created: new Date(),
                source: 'ai_generated'
            });
        }
        return flashcards;
    }
    
    static parseQuestionsResponse(response, settings) {
        // Mock parsing for demo - replace with actual AI response parsing
        const questions = [];
        for (let i = 0; i < settings.questionCount; i++) {
            questions.push({
                id: Date.now() + i,
                question: `AI-generated multiple choice question ${i + 1}?`,
                options: [
                    `Option A for question ${i + 1}`,
                    `Option B for question ${i + 1}`,
                    `Option C for question ${i + 1}`,
                    `Option D for question ${i + 1}`
                ],
                correctAnswer: Math.floor(Math.random() * 4),
                difficulty: settings.difficulty,
                topic: settings.topic || 'Study Topic',
                explanation: `This is the explanation for why this answer is correct for question ${i + 1}`,
                created: new Date(),
                source: 'ai_generated'
            });
        }
        return questions;
    }
    
    // Mock content generation for development/demo
    static generateMockFlashcards(content, topic, settings) {
        const keywords = this.extractKeywords(content);
        const flashcards = [];
        
        for (let i = 0; i < Math.min(settings.cardCount, 10); i++) {
            const keyword = keywords[i % keywords.length] || 'concept';
            flashcards.push({
                id: Date.now() + i,
                question: `What is ${keyword} in the context of ${topic}?`,
                answer: `${keyword} is an important aspect of ${topic} that helps understand the fundamental principles and applications in this field.`,
                difficulty: settings.difficulty,
                topic: topic,
                created: new Date(),
                source: 'mock_generated'
            });
        }
        
        return flashcards;
    }
    
    static generateMockQuestions(content, topic, settings) {
        const questions = [];
        
        for (let i = 0; i < Math.min(settings.questionCount, 5); i++) {
            questions.push({
                id: Date.now() + i,
                question: `Which statement about ${topic} is most accurate?`,
                options: [
                    `${topic} is primarily theoretical in nature`,
                    `${topic} has significant practical applications`,
                    `${topic} is an outdated concept`,
                    `${topic} is too complex for practical use`
                ],
                correctAnswer: 1,
                difficulty: settings.difficulty,
                topic: topic,
                explanation: `${topic} is known for having significant practical applications in real-world scenarios.`,
                created: new Date(),
                source: 'mock_generated'
            });
        }
        
        return questions;
    }
    
    static extractKeywords(text) {
        // Simple keyword extraction - in production, use more sophisticated NLP
        const words = text.toLowerCase()
            .replace(/[^\w\s]/g, '')
            .split(/\s+/)
            .filter(word => word.length > 4)
            .filter(word => !['this', 'that', 'with', 'from', 'they', 'were', 'been', 'have', 'their', 'said', 'each', 'which', 'what', 'where', 'when'].includes(word));
        
        // Get unique words and return top 10
        return [...new Set(words)].slice(0, 10);
    }
}

// Backend API Communication
class BackendAPI {
    static async makeRequest(endpoint, method = 'GET', data = null) {
        const token = localStorage.getItem('brainypal_token');
        
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };
        
        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(API_CONFIG.baseURL + endpoint, config);
            
            if (response.status === 401) {
                // Token expired, redirect to login
                handleLogout();
                throw new Error('Authentication required');
            }
            
            const responseData = await response.json();
            
            if (!response.ok) {
                throw new Error(responseData.message || 'Request failed');
            }
            
            return responseData;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // Specific API calls
    static async generateContent(formData) {
        return this.makeRequest('/generate', 'POST', formData);
    }
    
    static async saveProgress(progressData) {
        return this.makeRequest('/progress', 'POST', progressData);
    }
    
    static async getUserProgress() {
        return this.makeRequest('/progress', 'GET');
    }
    
    static async saveFlashcards(flashcards) {
        return this.makeRequest('/flashcards', 'POST', { flashcards });
    }
    
    static async getFlashcards() {
        return this.makeRequest('/flashcards', 'GET');
    }
    
    static async saveQuizResults(results) {
        return this.makeRequest('/quiz-results', 'POST', results);
    }
    
    static async getAnalytics() {
        return this.makeRequest('/analytics', 'GET');
    }
    
    static async processPayment(paymentData) {
        return this.makeRequest('/payment/process', 'POST', paymentData);
    }
    
    static async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const token = localStorage.getItem('brainypal_token');
        
        const response = await fetch(API_CONFIG.baseURL + '/upload', {
            method: 'POST',
            headers: {
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('File upload failed');
        }
        
        return response.json();
    }
}

// Advanced AI Features
class AdvancedAI {
    static async analyzeStudyContent(content) {
        // Analyze content difficulty, topics, key concepts
        try {
            const analysis = await this.callAnalysisAPI(content);
            return analysis;
        } catch (error) {
            console.error('Content analysis failed:', error);
            return this.mockContentAnalysis(content);
        }
    }
    
    static async callAnalysisAPI(content) {
        // Call AI API for content analysis
        const response = await fetch(`${AI_CONFIG.huggingFace.baseURL}/${AI_CONFIG.huggingFace.models.textClassification}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${AI_CONFIG.huggingFace.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                inputs: content
            })
        });
        
        return response.json();
    }
    
    static mockContentAnalysis(content) {
        const wordCount = content.split(/\s+/).length;
        const difficulty = wordCount > 500 ? 'advanced' : wordCount > 200 ? 'intermediate' : 'beginner';
        
        return {
            difficulty,
            wordCount,
            estimatedReadTime: Math.ceil(wordCount / 200),
            topics: this.extractTopics(content),
            keyTerms: this.extractKeyTerms(content)
        };
    }
    
    static extractTopics(content) {
        // Simple topic extraction - in production, use more sophisticated NLP
        const sentences = content.split(/[.!?]+/);
        const topics = sentences.slice(0, 3).map((sentence, index) => ({
            topic: `Topic ${index + 1}`,
            confidence: Math.random() * 0.4 + 0.6
        }));
        
        return topics;
    }
    
    static extractKeyTerms(content) {
        // Extract key terms from content
        const words = content.toLowerCase()
            .replace(/[^\w\s]/g, '')
            .split(/\s+/)
            .filter(word => word.length > 5);
        
        const frequency = {};
        words.forEach(word => {
            frequency[word] = (frequency[word] || 0) + 1;
        });
        
        return Object.entries(frequency)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .map(([term, count]) => ({ term, frequency: count }));
    }
    
    static async generatePersonalizedContent(userHistory, currentContent) {
        // Generate content based on user's learning history and preferences
        const preferences = this.analyzeUserPreferences(userHistory);
        return this.adaptContentToPreferences(currentContent, preferences);
    }
    
    static analyzeUserPreferences(history) {
        // Analyze user's past performance to understand preferences
        const difficulties = history.map(item => item.difficulty);
        const topics = history.map(item => item.topic);
        const performance = history.map(item => item.score || 0);
        
        return {
            preferredDifficulty: this.mostFrequent(difficulties),
            strongTopics: this.getTopPerformingTopics(topics, performance),
            weakTopics: this.getWeakTopics(topics, performance),
            averageScore: performance.reduce((a, b) => a + b, 0) / performance.length
        };
    }
    
    static mostFrequent(array) {
        const frequency = {};
        array.forEach(item => {
            frequency[item] = (frequency[item] || 0) + 1;
        });
        
        return Object.entries(frequency)
            .sort(([,a], [,b]) => b - a)[0]?.[0] || 'intermediate';
    }
    
    static getTopPerformingTopics(topics, scores) {
        const topicScores = {};
        topics.forEach((topic, index) => {
            if (!topicScores[topic]) {
                topicScores[topic] = { total: 0, count: 0 };
            }
            topicScores[topic].total += scores[index] || 0;
            topicScores[topic].count++;
        });
        
        return Object.entries(topicScores)
            .map(([topic, data]) => ({ topic, average: data.total / data.count }))
            .filter(item => item.average > 75)
            .sort((a, b) => b.average - a.average)
            .slice(0, 5);
    }
    
    static getWeakTopics(topics, scores) {
        const topicScores = {};
        topics.forEach((topic, index) => {
            if (!topicScores[topic]) {
                topicScores[topic] = { total: 0, count: 0 };
            }
            topicScores[topic].total += scores[index] || 0;
            topicScores[topic].count++;
        });
        
        return Object.entries(topicScores)
            .map(([topic, data]) => ({ topic, average: data.total / data.count }))
            .filter(item => item.average < 60)
            .sort((a, b) => a.average - b.average)
            .slice(0, 5);
    }
    
    static adaptContentToPreferences(content, preferences) {
        // Adapt content generation based on user preferences
        // This would involve more sophisticated AI in production
        return {
            recommendedDifficulty: preferences.preferredDifficulty,
            focusAreas: preferences.weakTopics.map(t => t.topic),
            reinforceAreas: preferences.strongTopics.map(t => t.topic)
        };
    }
}

// Spaced Repetition Algorithm
class SpacedRepetition {
    static calculateNextReview(performance, previousInterval = 1) {
        // SM-2 algorithm implementation
        const quality = performance; // 0-5 scale
        
        let easeFactor = 2.5;
        let interval = previousInterval;
        
        if (quality >= 3) {
            if (interval === 1) {
                interval = 6;
            } else {
                interval = Math.round(interval * easeFactor);
            }
            easeFactor = easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
        } else {
            interval = 1;
        }
        
        easeFactor = Math.max(1.3, easeFactor);
        
        return {
            nextReviewDate: new Date(Date.now() + interval * 24 * 60 * 60 * 1000),
            interval,
            easeFactor
        };
    }
    
    static getDueCards(flashcards) {
        const now = new Date();
        return flashcards.filter(card => {
            const nextReview = new Date(card.nextReview || 0);
            return nextReview <= now;
        });
    }
    
    static updateCardSchedule(cardId, performance) {
        const card = appState.studyData.flashcards.find(c => c.id === cardId);
        if (!card) return;
        
        const schedule = this.calculateNextReview(performance, card.interval || 1);
        
        card.nextReview = schedule.nextReviewDate;
        card.interval = schedule.interval;
        card.easeFactor = schedule.easeFactor;
        card.reviewCount = (card.reviewCount || 0) + 1;
        card.lastReviewed = new Date();
        
        // Save updated data
        saveUserData();
    }
}

// Real-time AI Chat Feature (Premium)
class AIChatTutor {
    static async askQuestion(question, context = '') {
        try {
            const response = await this.callChatAPI(question, context);
            return response;
        } catch (error) {
            console.error('AI Chat error:', error);
            return this.mockChatResponse(question);
        }
    }
    
    static async callChatAPI(question, context) {
        const prompt = `Context: ${context}\n\nQuestion: ${question}\n\nProvide a helpful, educational response:`;
        
        const response = await fetch(`${AI_CONFIG.huggingFace.baseURL}/${AI_CONFIG.huggingFace.models.textGeneration}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${AI_CONFIG.huggingFace.apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                inputs: prompt,
                parameters: {
                    max_length: 200,
                    temperature: 0.7,
                    do_sample: true,
                    return_full_text: false
                }
            })
        });
        
        const data = await response.json();
        return data[0]?.generated_text || this.mockChatResponse(question);
    }
    
    static mockChatResponse(question) {
        const responses = [
            "That's a great question! Let me help you understand this concept better.",
            "I can see why this might be confusing. Let me break it down for you.",
            "This is an important topic. Here's what you need to know:",
            "Good thinking! This connects to several key concepts we've studied."
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        return `${randomResponse} Based on your study materials, I can provide some insights to help clarify this topic.`;
    }
    
    static async generateFollowUpQuestions(topic, currentQuestion) {
        const followUps = [
            `Can you give me an example of ${topic} in real life?`,
            `How does ${topic} relate to other concepts we've studied?`,
            `What are the key components of ${topic}?`,
            `Why is ${topic} important to understand?`,
            `What are common misconceptions about ${topic}?`
        ];
        
        return followUps.slice(0, 3);
    }
}

// Performance Analytics
class PerformanceAnalytics {
    static generateStudyReport(timeframe = 'week') {
        const data = appState.studyData;
        const activities = data.recentActivity || [];
        
        return {
            timeframe,
            studyTime: this.calculateStudyTime(activities, timeframe),
            cardsReviewed: this.countCardsReviewed(activities, timeframe),
            quizzesTaken: this.countQuizzes(activities, timeframe),
            accuracy: this.calculateAccuracy(data.progress),
            streakInfo: this.getStreakInfo(data.progress),
            topTopics: this.getTopTopics(data.flashcards),
            recommendations: this.generateRecommendations(data)
        };
    }
    
    static calculateStudyTime(activities, timeframe) {
        const cutoff = this.getTimeframeCutoff(timeframe);
        const studyActivities = activities.filter(a => 
            a.type === 'study' && new Date(a.timestamp) > cutoff
        );
        
        // Estimate 2 minutes per card studied
        return studyActivities.length * 2;
    }
    
    static countCardsReviewed(activities, timeframe) {
        const cutoff = this.getTimeframeCutoff(timeframe);
        return activities.filter(a => 
            a.type === 'study' && new Date(a.timestamp) > cutoff
        ).length;
    }
    
    static countQuizzes(activities, timeframe) {
        const cutoff = this.getTimeframeCutoff(timeframe);
        return activities.filter(a => 
            a.type === 'quiz' && new Date(a.timestamp) > cutoff
        ).length;
    }
    
    static calculateAccuracy(progress) {
        if (!progress.totalQuestions) return 0;
        return Math.round((progress.correctAnswers / progress.totalQuestions) * 100);
    }
    
    static getStreakInfo(progress) {
        return {
            current: progress.streak || 0,
            longest: progress.longestStreak || progress.streak || 0
        };
    }
    
    static getTopTopics(flashcards) {
        const topicCount = {};
        flashcards.forEach(card => {
            topicCount[card.topic] = (topicCount[card.topic] || 0) + 1;
        });
        
        return Object.entries(topicCount)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 5)
            .map(([topic, count]) => ({ topic, count }));
    }
    
    static generateRecommendations(data) {
        const recommendations = [];
        
        if (data.progress.streak === 0) {
            recommendations.push({
                type: 'motivation',
                message: 'Start a study streak! Try to study at least one card daily.',
                action: 'study'
            });
        }
        
        if (data.progress.totalQuestions < 10) {
            recommendations.push({
                type: 'practice',
                message: 'Take more practice quizzes to improve your retention.',
                action: 'quiz'
            });
        }
        
        const accuracy = this.calculateAccuracy(data.progress);
        if (accuracy < 70) {
            recommendations.push({
                type: 'review',
                message: 'Review your flashcards more frequently to improve accuracy.',
                action: 'review'
            });
        }
        
        return recommendations;
    }
    
    static getTimeframeCutoff(timeframe) {
        const now = new Date();
        const msInDay = 24 * 60 * 60 * 1000;
        
        switch (timeframe) {
            case 'day': return new Date(now - msInDay);
            case 'week': return new Date(now - 7 * msInDay);
            case 'month': return new Date(now - 30 * msInDay);
            default: return new Date(now - 7 * msInDay);
        }
    }
}

// Export Management
class ExportManager {
    static async exportToAnki(flashcards) {
        const ankiFormat = flashcards.map(card => 
            `"${card.question}"\t"${card.answer}"\t"${card.topic}"`
        ).join('\n');
        
        const blob = new Blob([ankiFormat], { type: 'text/plain' });
        this.downloadFile(blob, 'brainypal_flashcards.txt');
    }
    
    static async exportToPDF(flashcards) {
        // In a real app, you would use a PDF library like jsPDF
        const content = flashcards.map(card => 
            `Q: ${card.question}\nA: ${card.answer}\n\n`
        ).join('');
        
        const blob = new Blob([content], { type: 'text/plain' });
        this.downloadFile(blob, 'brainypal_flashcards.pdf');
        
        showNotification('PDF export complete! 📄');
    }
    
    static async exportToJSON(data) {
        const exportData = {
            flashcards: data.flashcards,
            quizQuestions: data.quizQuestions,
            progress: data.progress,
            exportDate: new Date().toISOString(),
            version: '1.0'
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
            type: 'application/json' 
        });
        this.downloadFile(blob, 'brainypal_data.json');
    }
    
    static downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Content Quality Checker
class ContentQualityChecker {
    static analyzeGeneratedContent(content, type) {
        const analysis = {
            quality: 'good',
            issues: [],
            suggestions: []
        };
        
        if (type === 'flashcard') {
            this.checkFlashcardQuality(content, analysis);
        } else if (type === 'question') {
            this.checkQuestionQuality(content, analysis);
        }
        
        return analysis;
    }
    
    static checkFlashcardQuality(card, analysis) {
        if (card.question.length < 10) {
            analysis.issues.push('Question is too short');
            analysis.quality = 'poor';
        }
        
        if (card.answer.length < 20) {
            analysis.issues.push('Answer lacks detail');
            analysis.suggestions.push('Add more explanation to the answer');
        }
        
        if (card.question.includes('?') === false) {
            analysis.issues.push('Question should end with a question mark');
        }
        
        if (card.question.toLowerCase() === card.answer.toLowerCase()) {
            analysis.issues.push('Question and answer are too similar');
            analysis.quality = 'poor';
        }
    }
    
    static checkQuestionQuality(question, analysis) {
        if (question.options.length !== 4) {
            analysis.issues.push('Question should have exactly 4 options');
            analysis.quality = 'poor';
        }
        
        const optionLengths = question.options.map(opt => opt.length);
        const avgLength = optionLengths.reduce((a, b) => a + b) / optionLengths.length;
        
        if (Math.max(...optionLengths) > avgLength * 2) {
            analysis.issues.push('Option lengths are too varied');
            analysis.suggestions.push('Make options more consistent in length');
        }
        
        if (question.correctAnswer < 0 || question.correctAnswer >= question.options.length) {
            analysis.issues.push('Invalid correct answer index');
            analysis.quality = 'poor';
        }
    }
}

// Integration with main application
async function processGenerationRequest(formData) {
    try {
        showNotification('Processing your request...', 'info');
        
        let content = '';
        
        // Process input content
        if (formData.method === 'text') {
            content = formData.content;
        } else if (formData.method === 'file' && formData.files) {
            // Process uploaded files
            const fileTexts = await Promise.all(
                formData.files.map(async (fileItem) => {
                    const fileName = fileItem.querySelector('.file-name').textContent;
                    // In a real app, you would retrieve the actual file
                    return await FileProcessor.processFile({ name: fileName, type: 'text/plain' });
                })
            );
            content = fileTexts.join('\n\n');
        }
        
        // Analyze content
        const analysis = await AdvancedAI.analyzeStudyContent(content);
        showNotification(`Content analyzed: ${analysis.difficulty} level, ${analysis.wordCount} words`, 'info');
        
        // Generate flashcards and questions
        const [flashcards, questions] = await Promise.all([
            AIContentGenerator.generateFlashcards(content, formData.topic, formData.settings),
            AIContentGenerator.generateQuestions(content, formData.topic, formData.settings)
        ]);
        
        // Quality check
        flashcards.forEach(card => {
            const quality = ContentQualityChecker.analyzeGeneratedContent(card, 'flashcard');
            if (quality.issues.length > 0) {
                console.warn('Flashcard quality issues:', quality.issues);
            }
        });
        
        questions.forEach(question => {
            const quality = ContentQualityChecker.analyzeGeneratedContent(question, 'question');
            if (quality.issues.length > 0) {
                console.warn('Question quality issues:', quality.issues);
            }
        });
        
        return {
            success: true,
            data: {
                flashcards,
                questions,
                analysis
            }
        };
        
    } catch (error) {
        console.error('Content generation failed:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Background sync functionality
class BackgroundSync {
    static async syncData() {
        if (!navigator.onLine) {
            console.log('Offline, skipping sync');
            return;
        }
        
        try {
            const localData = {
                flashcards: appState.studyData.flashcards,
                progress: appState.studyData.progress,
                recentActivity: appState.studyData.recentActivity
            };
            
            await BackendAPI.saveProgress(localData);
            console.log('Data synced successfully');
        } catch (error) {
            console.error('Sync failed:', error);
        }
    }
    
    static startPeriodicSync() {
        // Sync every 5 minutes
        setInterval(() => {
            this.syncData();
        }, 5 * 60 * 1000);
        
        // Sync when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.syncData();
            }
        });
        
        // Sync before page unload
        window.addEventListener('beforeunload', () => {
            this.syncData();
        });
    }
}

// Initialize AI integration when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Start background sync
    BackgroundSync.startPeriodicSync();
    
    // Initialize AI features for premium users
    if (isPremiumUser()) {
        console.log('Premium AI features enabled');
    }
    
    // Check if APIs are properly configured
    if (AI_CONFIG.huggingFace.apiKey === 'YOUR_HUGGING_FACE_API_KEY') {
        console.warn('Hugging Face API key not configured. Using mock data.');
    }
});

// Global error handling for AI operations
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason.message?.includes('API') || event.reason.message?.includes('AI')) {
        console.error('AI operation failed:', event.reason);
        showNotification('AI service temporarily unavailable. Using fallback generation.', 'error');
        event.preventDefault();
    }
});

// Export AI integration functions
window.BrainyPalAI = {
    FileProcessor,
    AIContentGenerator,
    BackendAPI,
    AdvancedAI,
    SpacedRepetition,
    AIChatTutor,
    PerformanceAnalytics,
    ExportManager,
    ContentQualityChecker,
    processGenerationRequest
};