import React, { useState, useEffect, useRef } from 'react';
import { Send, MessageCircle, Brain, User, Clock, Search, History, Trash2 } from 'lucide-react';

const Chat = ({ user }) => {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Sample questions to help users get started
  const sampleQuestions = [
    "What is photosynthesis and how does it work?",
    "Explain the water cycle in simple terms",
    "How do computers process information?",
    "What causes earthquakes?",
    "Explain the concept of gravity",
    "How do vaccines work in the human body?",
    "What is artificial intelligence?",
    "Describe the process of digestion"
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
    // Add welcome message
    if (messages.length === 0) {
      setMessages([{
        id: 1,
        content: `Hello ${user?.email || 'there'}! I'm your AI study companion. Ask me anything - from science and math to history and literature. I'm here to help you learn! 🧠✨`,
        isUser: false,
        timestamp: new Date(),
        confidence: 1.0
      }]);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/chat/conversations', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!currentMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      content: currentMessage,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: currentMessage,
          conversation_id: currentConversationId
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setCurrentConversationId(data.conversation_id);
        
        const aiMessage = {
          id: data.ai_response.id,
          content: data.ai_response.content,
          isUser: false,
          timestamp: new Date(data.ai_response.timestamp),
          confidence: data.ai_response.confidence,
          processingTime: data.ai_response.processing_time
        };
        
        setMessages(prev => [...prev, aiMessage]);
        loadConversations(); // Refresh conversations list
      } else {
        throw new Error(data.error);
      }
    } catch (error) {
      // Fallback response for demo
      const aiMessage = {
        id: Date.now() + 1,
        content: generateFallbackResponse(currentMessage),
        isUser: false,
        timestamp: new Date(),
        confidence: 0.8
      };
      setMessages(prev => [...prev, aiMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateFallbackResponse = (question) => {
    const responses = {
      'photosynthesis': 'Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen. It occurs in two main stages: light-dependent reactions in the thylakoids and light-independent reactions (Calvin cycle) in the stroma of chloroplasts.',
      'water cycle': 'The water cycle is the continuous movement of water on Earth. It includes evaporation from oceans and rivers, condensation into clouds, precipitation as rain or snow, and collection back into water bodies. This process is driven by solar energy.',
      'computer': 'Computers process information through a series of steps: input (keyboard, mouse), processing (CPU performs calculations using binary code), storage (RAM for temporary, hard drive for permanent), and output (screen, speakers). The CPU executes instructions in machine language.',
      'earthquake': 'Earthquakes occur when tectonic plates suddenly slip past each other along fault lines. This releases stored energy as seismic waves that shake the ground. Most earthquakes happen at plate boundaries where plates collide, separate, or slide past each other.',
      'gravity': 'Gravity is a fundamental force that attracts objects with mass toward each other. Einstein described it as the curvature of spacetime caused by mass and energy. On Earth, gravity gives objects weight and keeps us grounded with an acceleration of 9.8 m/s².',
      'vaccine': 'Vaccines work by training your immune system to recognize and fight specific diseases. They contain weakened or inactive parts of a pathogen, prompting your body to produce antibodies. If exposed to the real disease later, your immune system remembers and can quickly defend against it.',
      'ai': 'Artificial Intelligence (AI) is the simulation of human intelligence in machines. AI systems can learn from data, recognize patterns, make decisions, and solve problems. Types include machine learning, natural language processing, and computer vision.',
      'digestion': 'Digestion is the process of breaking down food into nutrients your body can absorb. It starts in the mouth with chewing and saliva, continues in the stomach with acid breakdown, and completes in the small intestine where nutrients are absorbed into the bloodstream.'
    };
    
    const key = Object.keys(responses).find(k => question.toLowerCase().includes(k));
    return responses[key] || `That's a great question about "${question}". This topic involves several key concepts that I'd be happy to explain in detail. Could you be more specific about which aspect you'd like to understand better?`;
  };

  const loadConversation = async (conversationId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/chat/conversation/${conversationId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentConversationId(conversationId);
        
        const loadedMessages = data.messages.map(msg => ({
          id: msg.id,
          content: msg.content,
          isUser: msg.is_user,
          timestamp: new Date(msg.timestamp),
          confidence: msg.confidence
        }));
        
        setMessages(loadedMessages);
        setShowHistory(false);
      }
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const startNewConversation = () => {
    setCurrentConversationId(null);
    setMessages([{
      id: Date.now(),
      content: "Hello! I'm ready for a new conversation. What would you like to learn about today?",
      isUser: false,
      timestamp: new Date(),
      confidence: 1.0
    }]);
    setShowHistory(false);
  };

  const askSampleQuestion = (question) => {
    setCurrentMessage(question);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conv.last_message.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (showHistory) {
    return (
      <div className="max-w-6xl mx-auto p-6">
        <div className="bg-white rounded-2xl shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-800 flex items-center">
                <History className="w-6 h-6 mr-2 text-teal-500" />
                Chat History
              </h2>
              <button
                onClick={() => setShowHistory(false)}
                className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
              >
                Back to Chat
              </button>
            </div>
            
            <div className="relative">
              <Search className="w-5 h-5 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search conversations..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          
          <div className="p-6">
            {filteredConversations.length === 0 ? (
              <div className="text-center py-12">
                <MessageCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No conversations found</p>
                <button
                  onClick={startNewConversation}
                  className="mt-4 px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
                >
                  Start Your First Chat
                </button>
              </div>
            ) : (
              <div className="grid gap-4">
                {filteredConversations.map(conv => (
                  <div
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className="p-4 border border-gray-200 rounded-lg hover:border-teal-300 hover:shadow-md cursor-pointer transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-800 mb-1">{conv.title}</h3>
                        <p className="text-sm text-gray-600 mb-2">{conv.last_message}</p>
                        <div className="flex items-center text-xs text-gray-400 space-x-4">
                          <span className="flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {new Date(conv.updated_at).toLocaleDateString()}
                          </span>
                          <span>{conv.message_count} messages</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            loadConversation(conv.id);
                          }}
                          className="p-2 text-teal-500 hover:bg-teal-50 rounded-lg transition-colors"
                        >
                          <MessageCircle className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-2xl shadow-lg h-[80vh] flex flex-col">
        {/* Chat Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Brain className="w-8 h-8 text-teal-500 mr-3" />
              <div>
                <h2 className="text-xl font-bold text-gray-800">AI Study Assistant</h2>
                <p className="text-sm text-gray-600">Ask me anything - I'm here to help you learn!</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowHistory(true)}
                className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                title="View Chat History"
              >
                <History className="w-5 h-5" />
              </button>
              <button
                onClick={startNewConversation}
                className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
              >
                New Chat
              </button>
            </div>
          </div>
        </div>

        {/* Sample Questions */}
        {messages.length <= 1 && (
          <div className="p-6 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Try asking about:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sampleQuestions.slice(0, 6).map((question, index) => (
                <button
                  key={index}
                  onClick={() => askSampleQuestion(question)}
                  className="text-left p-3 bg-gray-50 hover:bg-teal-50 hover:border-teal-200 border border-gray-200 rounded-lg text-sm text-gray-700 hover:text-teal-700 transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.isUser ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex items-start space-x-3 max-w-[80%]`}>
                {!message.isUser && (
                  <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Brain className="w-4 h-4 text-teal-600" />
                  </div>
                )}
                
                <div
                  className={`px-4 py-3 rounded-2xl ${
                    message.isUser
                      ? 'bg-teal-500 text-white ml-auto'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className={`text-xs mt-2 opacity-70 flex items-center space-x-2 ${
                    message.isUser ? 'text-teal-100' : 'text-gray-500'
                  }`}>
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {!message.isUser && message.confidence && (
                      <span>• Confidence: {Math.round(message.confidence * 100)}%</span>
                    )}
                    {message.processingTime && (
                      <span>• {message.processingTime.toFixed(1)}s</span>
                    )}
                  </div>
                </div>

                {message.isUser && (
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-blue-600" />
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-start space-x-3 max-w-[80%]">
                <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center">
                  <Brain className="w-4 h-4 text-teal-600" />
                </div>
                <div className="px-4 py-3 rounded-2xl bg-gray-100">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-teal-500"></div>
                    <span className="text-gray-600">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        <div className="p-6 border-t border-gray-200">
          <form onSubmit={sendMessage} className="flex space-x-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                placeholder="Ask me anything about science, math, history, or any topic..."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent pr-12"
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                disabled={isLoading}
              />
              <div className="absolute right-3 top-3 text-xs text-gray-400">
                {currentMessage.length}/500
              </div>
            </div>
            <button
              type="submit"
              disabled={!currentMessage.trim() || isLoading}
              className="px-6 py-3 bg-teal-500 text-white rounded-xl hover:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <div className="mt-2 text-xs text-gray-500 text-center">
            💡 Tip: I can explain complex topics, solve problems, and help you understand any subject!
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;