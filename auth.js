import React, { useState } from 'react';
import { Brain, Mail, Lock, Eye, EyeOff, ArrowRight } from 'lucide-react';

const Auth = ({ onLogin }) => {
  const [currentView, setCurrentView] = useState('login');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [verificationStep, setVerificationStep] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [generatedCode, setGeneratedCode] = useState('');
  
  const [loginForm, setLoginForm] = useState({ 
    email: '', 
    password: '',
    code: '' 
  });
  
  const [signupForm, setSignupForm] = useState({ 
    email: '', 
    password: '', 
    confirmPassword: '' 
  });

  // Generate 6-digit verification code
  const generateVerificationCode = () => {
    return Math.floor(100000 + Math.random() * 900000).toString();
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (signupForm.password !== signupForm.confirmPassword) {
      alert('Passwords do not match!');
      return;
    }
    
    if (signupForm.password.length < 6) {
      alert('Password must be at least 6 characters long');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: signupForm.email,
          password: signupForm.password
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        // Generate and show verification code
        const code = generateVerificationCode();
        setGeneratedCode(code);
        setVerificationStep(true);
        
        // Simulate sending email (in real app, backend sends email)
        alert(`Verification code sent to ${signupForm.email}: ${code}`);
      } else {
        alert(data.error || 'Signup failed');
      }
    } catch (error) {
      alert('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    
    if (verificationCode !== generatedCode) {
      alert('Invalid verification code!');
      return;
    }

    setIsLoading(true);
    
    try {
      // In real implementation, send code to backend for verification
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: signupForm.email,
          code: verificationCode
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user);
      } else {
        alert('Verification failed');
      }
    } catch (error) {
      // For demo, just proceed if code is correct
      const userData = {
        email: signupForm.email,
        id: Date.now(),
        plan: 'free'
      };
      localStorage.setItem('user', JSON.stringify(userData));
      onLogin(userData);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: loginForm.email,
          password: loginForm.password
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user);
      } else {
        alert(data.error || 'Login failed');
      }
    } catch (error) {
      // Demo login - remove in production
      const userData = {
        email: loginForm.email,
        id: Date.now(),
        plan: 'premium'
      };
      localStorage.setItem('user', JSON.stringify(userData));
      onLogin(userData);
    } finally {
      setIsLoading(false);
    }
  };

  if (verificationStep) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-teal-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-4">
              <Brain className="w-10 h-10 text-teal-500" />
              <span className="ml-2 text-2xl font-bold text-gray-800">BrainyPal</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-800">Verify Your Email</h3>
            <p className="text-sm text-gray-600 mt-2">
              Enter the 6-digit code sent to<br/>
              <strong>{signupForm.email}</strong>
            </p>
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Demo Code:</strong> {generatedCode}
              </p>
            </div>
          </div>

          <form onSubmit={handleVerifyCode} className="space-y-6">
            <div>
              <input
                type="text"
                placeholder="Enter 6-digit verification code"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent text-center text-xl tracking-widest font-mono"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || verificationCode.length !== 6}
              className="w-full bg-teal-500 text-white py-3 rounded-lg font-medium hover:bg-teal-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  Verify & Continue
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </button>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => {
                  setVerificationStep(false);
                  setVerificationCode('');
                }}
                className="flex-1 text-gray-600 py-2 text-sm hover:text-gray-800"
              >
                Back to Sign Up
              </button>
              
              <button
                type="button"
                onClick={() => {
                  const newCode = generateVerificationCode();
                  setGeneratedCode(newCode);
                  alert(`New code sent: ${newCode}`);
                }}
                className="flex-1 text-teal-500 py-2 text-sm hover:text-teal-600"
              >
                Resend Code
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-teal-500 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Brain className="w-10 h-10 text-teal-500" />
            <span className="ml-2 text-2xl font-bold text-gray-800">BrainyPal</span>
          </div>
          <p className="text-gray-600">Your AI-Powered Study Companion</p>
          <div className="mt-4 p-3 bg-amber-50 rounded-lg">
            <p className="text-sm text-amber-800">
              🚀 Now with verification codes, chat history, and dynamic content generation!
            </p>
          </div>
        </div>

        <div className="flex space-x-2 mb-6">
          <button 
            onClick={() => setCurrentView('login')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
              currentView === 'login' 
                ? 'bg-teal-500 text-white shadow-lg' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Login
          </button>
          <button 
            onClick={() => setCurrentView('signup')}
            className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
              currentView === 'signup' 
                ? 'bg-teal-500 text-white shadow-lg' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Sign Up
          </button>
        </div>

        {currentView === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="relative">
              <Mail className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="email"
                placeholder="Email address"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                value={loginForm.email}
                onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
                required
              />
            </div>
            
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                value={loginForm.password}
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-teal-500 text-white py-3 rounded-lg font-medium hover:bg-teal-600 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="relative">
              <Mail className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="email"
                placeholder="Email address"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                value={signupForm.email}
                onChange={(e) => setSignupForm({...signupForm, email: e.target.value})}
                required
              />
            </div>
            
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password (min 6 characters)"
                className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                value={signupForm.password}
                onChange={(e) => setSignupForm({...signupForm, password: e.target.value})}
                minLength={6}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
            
            <div className="relative">
              <Lock className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="password"
                placeholder="Confirm Password"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                value={signupForm.confirmPassword}
                onChange={(e) => setSignupForm({...signupForm, confirmPassword: e.target.value})}
                required
              />
            </div>
            
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-teal-500 text-white py-3 rounded-lg font-medium hover:bg-teal-600 transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  Create Account
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Auth;