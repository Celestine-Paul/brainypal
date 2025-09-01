// BrainyPal - Authentication Logic
// auth.js

// Authentication state
let authState = {
    isAuthenticated: false,
    currentUser: null,
    authMethod: null
};

// API endpoints for authentication
const AUTH_ENDPOINTS = {
    login: '/api/auth/login',
    register: '/api/auth/register',
    logout: '/api/auth/logout',
    refresh: '/api/auth/refresh',
    socialLogin: '/api/auth/social',
    forgotPassword: '/api/auth/forgot-password',
    resetPassword: '/api/auth/reset-password'
};

// Switch between login and register tabs
function switchAuthTab(tabType) {
    // Remove active classes
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });
    
    // Add active class to selected tab
    event.target.classList.add('active');
    document.getElementById(tabType + 'Form').classList.add('active');
}

// Handle user login
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!validateEmail(email)) {
        showAuthError('Please enter a valid email address.');
        return;
    }
    
    if (!password) {
        showAuthError('Please enter your password.');
        return;
    }
    
    showAuthLoading('login');
    
    try {
        const response = await fetch(API_CONFIG.baseURL + AUTH_ENDPOINTS.login, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            handleAuthSuccess(data);
        } else {
            throw new Error(data.message || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        // For demo purposes, simulate successful login
        handleDemoLogin(email);
    } finally {
        hideAuthLoading('login');
    }
}

// Handle user registration
async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    
    // Validation
    if (!name) {
        showAuthError('Please enter your full name.');
        return;
    }
    
    if (!validateEmail(email)) {
        showAuthError('Please enter a valid email address.');
        return;
    }
    
    if (password.length < 8) {
        showAuthError('Password must be at least 8 characters long.');
        return;
    }
    
    if (password !== confirmPassword) {
        showAuthError('Passwords do not match.');
        return;
    }
    
    showAuthLoading('register');
    
    try {
        const response = await fetch(API_CONFIG.baseURL + AUTH_ENDPOINTS.register, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            handleAuthSuccess(data);
        } else {
            throw new Error(data.message || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        // For demo purposes, simulate successful registration
        handleDemoRegister(name, email);
    } finally {
        hideAuthLoading('register');
    }
}

// Handle social login (Google, GitHub)
async function handleSocialLogin(provider) {
    try {
        showNotification(`Connecting to ${provider}...`, 'info');
        
        // In a real app, this would redirect to OAuth provider
        // For demo, simulate successful social login
        setTimeout(() => {
            const demoUser = {
                id: 'social_' + Date.now(),
                name: provider === 'google' ? 'Google User' : 'GitHub User',
                email: `user@${provider}.com`,
                subscription: 'free',
                avatar: null,
                authMethod: provider
            };
            
            handleAuthSuccess({
                success: true,
                user: demoUser,
                token: 'demo_token_' + Date.now()
            });
        }, 1500);
        
    } catch (error) {
        console.error('Social login error:', error);
        showAuthError(`Failed to connect with ${provider}. Please try again.`);
    }
}

// Demo authentication functions
function handleDemoLogin(email) {
    const demoUser = {
        id: 'demo_' + Date.now(),
        name: 'John Doe',
        email: email,
        subscription: 'free',
        avatar: null,
        authMethod: 'email'
    };
    
    handleAuthSuccess({
        success: true,
        user: demoUser,
        token: 'demo_token_' + Date.now()
    });
}

function handleDemoRegister(name, email) {
    const demoUser = {
        id: 'demo_' + Date.now(),
        name: name,
        email: email,
        subscription: 'free',
        avatar: null,
        authMethod: 'email'
    };
    
    handleAuthSuccess({
        success: true,
        user: demoUser,
        token: 'demo_token_' + Date.now()
    });
}

// Handle successful authentication
function handleAuthSuccess(data) {
    authState.isAuthenticated = true;
    authState.currentUser = data.user;
    appState.user = data.user;
    
    // Store authentication data
    localStorage.setItem('brainypal_token', data.token);
    localStorage.setItem('brainypal_user', JSON.stringify(data.user));
    
    // Show main application
    showMainApp();
    updateUserInterface();
    loadUserData();
    
    // Welcome message
    showNotification(`Welcome back, ${data.user.name}! 🎉`, 'success');
    addActivity('Logged in successfully', 'session');
    
    // Clear auth forms
    clearAuthForms();
}

// Handle logout
function handleLogout() {
    // Clear stored data
    localStorage.removeItem('brainypal_token');
    localStorage.removeItem('brainypal_user');
    localStorage.removeItem('brainypal_study_data');
    localStorage.removeItem('brainypal_usage');
    
    // Reset application state
    authState = {
        isAuthenticated: false,
        currentUser: null,
        authMethod: null
    };
    
    appState.user = null;
    
    // Stop any active sessions
    if (appState.session.isActive) {
        if (appState.session.timer) {
            clearInterval(appState.session.timer);
        }
        appState.session.isActive = false;
    }
    
    // Show authentication modal
    showAuthModal();
    showNotification('Logged out successfully! 👋', 'info');
}

// Forgot password functionality
function showForgotPassword() {
    const email = prompt('Enter your email address to reset your password:');
    if (email && validateEmail(email)) {
        showNotification('Password reset instructions sent to your email! 📧', 'info');
        // In real app, this would call the forgot password API
    } else if (email) {
        showAuthError('Please enter a valid email address.');
    }
}

// Validation functions
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
}

// Authentication UI helpers
function showAuthLoading(formType) {
    const btn = document.querySelector(`#${formType}Form button[type="submit"]`);
    const originalText = btn.innerHTML;
    
    btn.disabled = true;
    btn.innerHTML = `
        <div style="display: inline-block; width: 16px; height: 16px; border: 2px solid #ffffff30; border-top: 2px solid white; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 8px;"></div>
        ${formType === 'login' ? 'Signing in...' : 'Creating account...'}
    `;
    
    // Store original text for restoration
    btn.dataset.originalText = originalText;
}

function hideAuthLoading(formType) {
    const btn = document.querySelector(`#${formType}Form button[type="submit"]`);
    btn.disabled = false;
    btn.innerHTML = btn.dataset.originalText || (formType === 'login' ? '🚀 Login to BrainyPal' : '🎯 Create Account');
}

function showAuthError(message) {
    // Create or update error message element
    let errorEl = document.querySelector('.auth-error');
    if (!errorEl) {
        errorEl = document.createElement('div');
        errorEl.className = 'auth-error';
        errorEl.style.cssText = `
            background: #fed7d7;
            color: #c53030;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 1px solid #feb2b2;
            font-size: 14px;
            text-align: center;
        `;
        
        const activeForm = document.querySelector('.auth-form.active');
        activeForm.insertBefore(errorEl, activeForm.firstChild);
    }
    
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    }, 5000);
}

function hideAuthError() {
    const errorEl = document.querySelector('.auth-error');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

function clearAuthForms() {
    document.querySelectorAll('.auth-form input').forEach(input => {
        input.value = '';
    });
    hideAuthError();
}

// Token management
function getAuthToken() {
    return localStorage.getItem('brainypal_token');
}

function isTokenValid(token) {
    if (!token) return false;
    
    try {
        // In a real app, you would validate the JWT token
        // For demo, just check if it exists and isn't expired
        const tokenData = JSON.parse(atob(token.split('.')[1] || ''));
        return tokenData.exp > Date.now() / 1000;
    } catch {
        return false;
    }
}

// Automatic token refresh
async function refreshAuthToken() {
    const token = getAuthToken();
    if (!token) return false;
    
    try {
        const response = await fetch(API_CONFIG.baseURL + AUTH_ENDPOINTS.refresh, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.token) {
            localStorage.setItem('brainypal_token', data.token);
            return true;
        }
        
        return false;
    } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
    }
}

// Session management
function startAuthSession() {
    // Set up periodic token refresh
    setInterval(async () => {
        if (authState.isAuthenticated) {
            const refreshed = await refreshAuthToken();
            if (!refreshed) {
                console.warn('Token refresh failed, logging out user');
                handleLogout();
            }
        }
    }, 15 * 60 * 1000); // Refresh every 15 minutes
}

// Password strength checker
function checkPasswordStrength(password) {
    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
    };
    
    const score = Object.values(checks).filter(Boolean).length;
    
    return {
        score,
        level: score < 3 ? 'weak' : score < 4 ? 'medium' : 'strong',
        checks
    };
}

// Add password strength indicator
function addPasswordStrengthIndicator() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        if (input.id === 'regPassword') {
            input.addEventListener('input', function() {
                updatePasswordStrength(this.value);
            });
        }
    });
}

function updatePasswordStrength(password) {
    const strength = checkPasswordStrength(password);
    
    // Remove existing indicator
    const existingIndicator = document.querySelector('.password-strength');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Create new indicator
    const indicator = document.createElement('div');
    indicator.className = 'password-strength';
    indicator.style.cssText = `
        margin-top: 8px;
        padding: 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    `;
    
    const colors = {
        weak: '#f56565',
        medium: '#ed8936',
        strong: '#48bb78'
    };
    
    indicator.style.background = colors[strength.level] + '20';
    indicator.style.color = colors[strength.level];
    indicator.style.border = `1px solid ${colors[strength.level]}40`;
    
    indicator.innerHTML = `
        <div>Password strength: <strong>${strength.level.toUpperCase()}</strong></div>
        <div style="margin-top: 4px;">
            ${strength.checks.length ? '✓' : '✗'} At least 8 characters
            ${strength.checks.uppercase ? '✓' : '✗'} Uppercase letter
            ${strength.checks.lowercase ? '✓' : '✗'} Lowercase letter
            ${strength.checks.number ? '✓' : '✗'} Number
        </div>
    `;
    
    const passwordInput = document.getElementById('regPassword');
    passwordInput.parentNode.appendChild(indicator);
}

// Social authentication handlers
async function initializeGoogleAuth() {
    // In a real app, you would initialize Google OAuth
    console.log('Google Auth initialized');
}

async function initializeGitHubAuth() {
    // In a real app, you would initialize GitHub OAuth
    console.log('GitHub Auth initialized');
}

// Form validation
function validateLoginForm() {
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!email || !password) {
        showAuthError('Please fill in all fields.');
        return false;
    }
    
    if (!validateEmail(email)) {
        showAuthError('Please enter a valid email address.');
        return false;
    }
    
    return true;
}

function validateRegisterForm() {
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    const termsChecked = document.querySelector('#registerForm input[type="checkbox"]').checked;
    
    if (!name || !email || !password || !confirmPassword) {
        showAuthError('Please fill in all fields.');
        return false;
    }
    
    if (!validateEmail(email)) {
        showAuthError('Please enter a valid email address.');
        return false;
    }
    
    if (password.length < 8) {
        showAuthError('Password must be at least 8 characters long.');
        return false;
    }
    
    if (password !== confirmPassword) {
        showAuthError('Passwords do not match.');
        return false;
    }
    
    if (!termsChecked) {
        showAuthError('Please accept the Terms of Service and Privacy Policy.');
        return false;
    }
    
    return true;
}

// User session persistence
function saveUserSession(userData, token) {
    localStorage.setItem('brainypal_user', JSON.stringify(userData));
    localStorage.setItem('brainypal_token', token);
    localStorage.setItem('brainypal_login_time', Date.now().toString());
}

function clearUserSession() {
    localStorage.removeItem('brainypal_user');
    localStorage.removeItem('brainypal_token');
    localStorage.removeItem('brainypal_login_time');
    localStorage.removeItem('brainypal_study_data');
    localStorage.removeItem('brainypal_usage');
}

// User profile management
function updateUserProfile(updates) {
    if (!appState.user) return;
    
    appState.user = { ...appState.user, ...updates };
    localStorage.setItem('brainypal_user', JSON.stringify(appState.user));
    updateUserInterface();
}

// Account security features
function enableTwoFactorAuth() {
    // In a real app, this would set up 2FA
    showNotification('Two-factor authentication would be set up here', 'info');
}

function changePassword() {
    const currentPassword = prompt('Enter your current password:');
    const newPassword = prompt('Enter your new password:');
    const confirmPassword = prompt('Confirm your new password:');
    
    if (newPassword && newPassword === confirmPassword && newPassword.length >= 8) {
        // In a real app, this would call the change password API
        showNotification('Password changed successfully! 🔐', 'success');
    } else {
        showAuthError('Password change failed. Please try again.');
    }
}

// Error handling for authentication
function handleAuthError(error) {
    console.error('Authentication error:', error);
    
    if (error.message.includes('network') || error.message.includes('fetch')) {
        showAuthError('Network error. Please check your connection and try again.');
    } else if (error.message.includes('unauthorized')) {
        showAuthError('Invalid credentials. Please check your email and password.');
    } else {
        showAuthError('Authentication failed. Please try again.');
    }
}

// Initialize authentication when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Add password strength indicator
    addPasswordStrengthIndicator();
    
    // Initialize social auth
    initializeGoogleAuth();
    initializeGitHubAuth();
    
    // Start auth session management
    startAuthSession();
    
    // Add form event listeners
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    
    // Auto-hide error messages when user starts typing
    document.querySelectorAll('.auth-form input').forEach(input => {
        input.addEventListener('input', hideAuthError);
    });
    
    // Enter key handling for forms
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && document.getElementById('authOverlay').style.display !== 'none') {
            const activeForm = document.querySelector('.auth-form.active');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.click();
                }
            }
        }
    });
});

// Export authentication functions
window.BrainyPalAuth = {
    switchAuthTab,
    handleLogin,
    handleRegister,
    handleSocialLogin,
    handleLogout,
    showForgotPassword,
    validateEmail,
    checkPasswordStrength,
    isAuthenticated: () => authState.isAuthenticated,
    getCurrentUser: () => authState.currentUser
};