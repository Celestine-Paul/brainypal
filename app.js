import React, { useState, useEffect } from 'react';
import { Brain, MessageCircle, BookOpen, History, User, Settings, Crown, LogOut, Menu, X } from 'lucide-react';

// Import components
import Auth from './Auth';
import Chat from './Chat';
import StudyMaterials from './StudyMaterials';
import Pricing from './Pricing';

const App = () => {
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('study');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing user session
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
    
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setCurrentView('study');
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    setUser(null);
    setCurrentView('study');
  };

  const handleUpgrade = (newPlan) => {
    const updatedUser = { ...user, plan: newPlan };
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
    setCurrentView('study');
  };

  const navigation = [
    {
      key: 'study',
      label: 'Study Materials',
      icon: BookOpen,
      description: 'Generate flashcards & quizzes'
    },
    {
      key: 'chat',
      label: 'AI Chat',
      icon: MessageCircle,
      description: 'Ask questions & get answers'
    },
    {
      key: 'history',
      label: 'History',
      icon: History,
      description: 'Review past conversations'
    },
    {
      key: 'pricing',
      label: 'Upgrade',
      icon: Crown,
      description: 'Premium features'
    }
  ];

  const getPlanIcon = (plan) => {
    switch (plan) {
      case 'premium':
        return <Crown className="w-4 h-4 text-blue-500" />;
      case 'pro':
        return <Crown className="w-4 h-4 text-purple-500" />;
      default:
        return <User className="w-4 h-4 text-gray-500" />;
    }
  };

  const getPlanColor = (plan) => {
    switch (plan) {
      case 'premium':
        return 'bg-blue-100 text-blue-800';
      case 'pro':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-teal-500 flex items-center justify-center">
        <div className="text-center text-white">
          <Brain className="w-16 h-16 mx-auto mb-4 animate-pulse" />
          <p className="text-xl">Loading BrainyPal...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-teal-500">
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-lg border-b border-white/20 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
              >
                {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
              <div className="flex items-center space-x-2">
                <Brain className="w-8 h-8 text-white" />
                <span className="text-2xl font-bold text-white">BrainyPal</span>
              </div>
              <div className="hidden md:block">
                <span className="text-white/80 text-sm">Your AI Learning Companion</span>
              </div>
            </div>
            
            {/* Navigation - Desktop */}
            <nav className="hidden md:flex items-center space-x-6">
              {navigation.map(({ key, label, icon: Icon, description }) => (
                <button
                  key={key}
                  onClick={() => setCurrentView(key)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all ${
                    currentView === key 
                      ? 'bg-white/20 text-white shadow-lg' 
                      : 'text-white/80 hover:text-white hover:bg-white/10'
                  }`}
                  title={description}
                >
                  <Icon className="w-5 h-5" />
                  <span>{label}</span>
                </button>
              ))}
            </nav>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              {/* Plan Badge */}
              <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center space-x-2 ${getPlanColor(user.plan)}`}>
                {getPlanIcon(user.plan)}
                <span className="capitalize">{user.plan}</span>
              </div>

              {/* User Dropdown */}
              <div className="relative group">
                <button className="flex items-center space-x-2 p-2 text-white hover:bg-white/10 rounded-lg transition-colors">
                  <User className="w-5 h-5" />
                  <span className="hidden sm:block">{user.email}</span>
                </button>
                
                {/* Dropdown Menu */}
                <div className="absolute right-0 top-full mt-2 w-56 bg-white rounded-xl shadow-xl border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                  <div className="p-4 border-b border-gray-100">
                    <p className="font-semibold text-gray-800" /p>