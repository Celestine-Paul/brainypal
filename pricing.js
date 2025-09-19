import React, { useState } from 'react';
import { Check, Star, Crown, Zap, Users, MessageCircle, Upload, Brain, History, Target } from 'lucide-react';

const Pricing = ({ user, onUpgrade }) => {
  const [selectedPlan, setSelectedPlan] = useState(user?.plan || 'free');
  const [isProcessing, setIsProcessing] = useState(false);

  const plans = [
    {
      id: 'free',
      name: 'Free',
      price: 0,
      currency: 'KSH',
      period: 'forever',
      description: 'Perfect for trying out BrainyPal',
      icon: Users,
      color: 'gray',
      popular: false,
      features: [
        '5 AI chat messages per day',
        'Generate 3 flashcard sets per day',
        'Basic quiz questions',
        'Upload 1 document per day',
        '7-day chat history',
        'Community support'
      ],
      limitations: [
        'Limited daily usage',
        'Basic AI responses',
        'No priority support',
        'Limited file uploads'
      ]
    },
    {
      id: 'premium',
      name: 'Premium',
      price: 500,
      currency: 'KSH',
      period: 'month',
      description: 'Best for students and regular learners',
      icon: Star,
      color: 'blue',
      popular: true,
      features: [
        'Unlimited AI chat messages',
        'Generate unlimited flashcards & quizzes',
        'Advanced quiz types (multiple choice, true/false)',
        'Upload unlimited documents (PDF, Word, Text)',
        'Complete chat history & search',
        'Dynamic content generation',
        'Progress tracking & analytics',
        'Email support',
        'Study session recording',
        'Topic mastery tracking'
      ],
      bonus: [
        '✨ NEW: Always different content on refresh',
        '🧠 Advanced AI responses',
        '📊 Detailed learning analytics'
      ]
    },
    {
      id: 'pro',
      name: 'Pro',
      price: 1000,
      currency: 'KSH',
      period: 'month',
      description: 'Perfect for serious students and professionals',
      icon: Crown,
      color: 'purple',
      popular: false,
      features: [
        'Everything in Premium',
        'Priority AI processing (faster responses)',
        'Advanced study analytics & insights',
        'Custom difficulty levels',
        'Bulk content generation',
        'Export flashcards & quizzes',
        'Study streak tracking',
        'Performance predictions',
        'Priority customer support',
        'Early access to new features'
      ],
      bonus: [
        '🚀 Lightning-fast AI responses',
        '📈 Advanced progress predictions',
        '🎯 Personalized study recommendations',
        '💼 Professional support'
      ]
    }
  ];

  const handleUpgrade = async (planId) => {
    if (planId === 'free' || planId === user?.plan) return;

    setIsProcessing(true);
    setSelectedPlan(planId);

    try {
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 2000));

      // In real app, integrate with payment provider (Stripe, Flutterwave, M-Pesa)
      const paymentData = {
        plan: planId,
        amount: plans.find(p => p.id === planId).price,
        currency: 'KSH',
        user_id: user?.id
      };

      // Simulate successful payment
      onUpgrade(planId);
      alert(`Successfully upgraded to ${plans.find(p => p.id === planId).name} plan!`);

    } catch (error) {
      alert('Payment failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const getPlanColor = (color, variant = 'bg') => {
    const colors = {
      gray: {
        bg: 'bg-gray-100',
        text: 'text-gray-600',
        button: 'bg-gray-500 hover:bg-gray-600',
        border: 'border-gray-300'
      },
      blue: {
        bg: 'bg-blue-100',
        text: 'text-blue-600',
        button: 'bg-blue-500 hover:bg-blue-600',
        border: 'border-blue-300'
      },
      purple: {
        bg: 'bg-purple-100',
        text: 'text-purple-600',
        button: 'bg-purple-500 hover:bg-purple-600',
        border: 'border-purple-300'
      }
    };
    return colors[color][variant];
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">Choose Your Learning Plan</h1>
        <p className="text-xl text-gray-600 mb-6">
          Unlock the full power of AI-driven learning with affordable Kenyan pricing
        </p>
        <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium">
          <span className="mr-2">🇰🇪</span>
          Pricing in Kenyan Shillings • M-Pesa payments accepted
        </div>
      </div>

      {/* Current Plan Status */}
      {user && (
        <div className="mb-8 p-4 bg-blue-50 rounded-xl">
          <div className="flex items-center justify-center space-x-2 text-blue-800">
            <Star className="w-5 h-5" />
            <span className="font-medium">
              Current Plan: <span className="capitalize">{user.plan}</span>
              {user.plan === 'free' && ' (Upgrade for unlimited access!)'}
            </span>
          </div>
        </div>
      )}

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-3 gap-8 mb-12">
        {plans.map((plan) => {
          const Icon = plan.icon;
          const isCurrentPlan = user?.plan === plan.id;
          const isUpgrade = plan.id !== 'free' && plan.id !== user?.plan;

          return (
            <div
              key={plan.id}
              className={`relative rounded-2xl p-8 transition-all duration-200 ${
                plan.popular 
                  ? 'border-2 border-blue-400 shadow-xl scale-105' 
                  : 'border border-gray-200 shadow-lg hover:shadow-xl'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-blue-500 text-white px-6 py-2 rounded-full text-sm font-bold">
                    Most Popular
                  </div>
                </div>
              )}

              {isCurrentPlan && (
                <div className="absolute -top-4 right-4">
                  <div className="bg-green-500 text-white px-4 py-2 rounded-full text-sm font-bold flex items-center">
                    <Check className="w-4 h-4 mr-1" />
                    Active
                  </div>
                </div>
              )}

              <div className="text-center mb-6">
                <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full ${getPlanColor(plan.color, 'bg')} mb-4`}>
                  <Icon className={`w-8 h-8 ${getPlanColor(plan.color, 'text')}`} />
                </div>
                
                <h3 className="text-2xl font-bold text-gray-800 mb-2">{plan.name}</h3>
                <p className="text-gray-600 mb-4">{plan.description}</p>
                
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-800">
                    {plan.price === 0 ? 'Free' : `${plan.currency} ${plan.price.toLocaleString()}`}
                  </span>
                  {plan.price > 0 && (
                    <span className="text-gray-600">/{plan.period}</span>
                  )}
                </div>
              </div>

              {/* Features */}
              <div className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-start">
                    <Check className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              {/* Bonus Features */}
              {plan.bonus && (
                <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
                  <h4 className="font-semibold text-yellow-800 mb-2">Bonus Features:</h4>
                  <div className="space-y-2">
                    {plan.bonus.map((bonus, index) => (
                      <p key={index} className="text-sm text-yellow-700">{bonus}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations for Free Plan */}
              {plan.limitations && (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-semibold text-gray-700 mb-2">Limitations:</h4>
                  <div className="space-y-2">
                    {plan.limitations.map((limitation, index) => (
                      <div key={index} className="flex items-start">
                        <span className="text-gray-400 mr-2">•</span>
                        <span className="text-sm text-gray-600">{limitation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Button */}
              <button
                onClick={() => handleUpgrade(plan.id)}
                disabled={isCurrentPlan || isProcessing}
                className={`w-full py-4 px-6 rounded-xl font-bold transition-all duration-200 ${
                  isCurrentPlan
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : isUpgrade
                    ? `${getPlanColor(plan.color, 'button')} text-white hover:shadow-lg transform hover:scale-105`
                    : 'bg-gray-500 text-white hover:bg-gray-600'
                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {isProcessing && selectedPlan === plan.id ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </div>
                ) : isCurrentPlan ? (
                  'Current Plan'
                ) : plan.id === 'free' ? (
                  'Get Started Free'
                ) : (
                  `Upgrade to ${plan.name}`
                )}
              </button>

              {/* Payment Methods for Paid Plans */}
              {plan.id !== 'free' && !isCurrentPlan && (
                <div className="mt-4 text-center">
                  <p className="text-xs text-gray-500 mb-2">Secure payment via:</p>
                  <div className="flex justify-center items-center space-x-2 text-xs text-gray-600">
                    <span>💳 M-Pesa</span>
                    <span>•</span>
                    <span>🏦 Card</span>
                    <span>•</span>
                    <span>📱 Airtel Money</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Feature Comparison */}
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Feature Comparison</h2>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-800">Features</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-600">Free</th>
                <th className="text-center py-3 px-4 font-semibold text-blue-600">Premium</th>
                <th className="text-center py-3 px-4 font-semibold text-purple-600">Pro</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[
                ['AI Chat Messages', '5/day', 'Unlimited', 'Unlimited + Priority'],
                ['Flashcard Generation', '3 sets/day', 'Unlimited', 'Unlimited + Bulk'],
                ['File Uploads', '1/day', 'Unlimited', 'Unlimited + Batch'],
                ['Chat History', '7 days', 'Forever', 'Forever + Advanced'],
                ['Content Variety', 'Basic', 'Always Different', 'Always Different + Custom'],
                ['Progress Analytics', 'Basic', 'Advanced', 'Professional'],
                ['Response Speed', 'Standard', 'Fast', 'Lightning Fast'],
                ['Support', 'Community', 'Email', 'Priority + Phone']
              ].map(([feature, free, premium, pro], index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium text-gray-800">{feature}</td>
                  <td className="py-3 px-4 text-center text-gray-600">{free}</td>
                  <td className="py-3 px-4 text-center text-blue-600 font-medium">{premium}</td>
                  <td className="py-3 px-4 text-center text-purple-600 font-medium">{pro}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* FAQ */}
      <div className="mt-12 bg-gray-50 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Frequently Asked Questions</h2>
        
        <div className="grid md:grid-cols-2 gap-6">
          {[
            {
              q: "Can I change my plan anytime?",
              a: "Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately."
            },
            {
              q: "Do you accept M-Pesa payments?",
              a: "Absolutely! We accept M-Pesa, Airtel Money, and international cards for your convenience."
            },
            {
              q: "Is my data safe and private?",
              a: "Yes, all your data is encrypted and stored securely. We never share your information with third parties."
            },
            {
              q: "Can I get a refund?",
              a: "We offer a 7-day money-back guarantee if you're not satisfied with your premium plan."
            },
            {
              q: "How does the AI generate different content?",
              a: "Our AI uses advanced algorithms to create unique flashcards and questions every time you generate content."
            },
            {
              q: "Is there a student discount?",
              a: "Yes! Contact our support team with your student ID for a 20% discount on all plans."
            }
          ].map(({ q, a }, index) => (
            <div key={index} className="p-4">
              <h3 className="font-semibold text-gray-800 mb-2">{q}</h3>
              <p className="text-gray-600 text-sm">{a}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Call to Action */}
      <div className="mt-12 text-center">
        <div className="bg-gradient-to-r from-teal-500 to-blue-500 rounded-2xl p-8 text-white">
          <h2 className="text-3xl font-bold mb-4">Ready to Supercharge Your Learning?</h2>
          <p className="text-xl opacity-90 mb-6">
            Join thousands of Kenyan students already using BrainyPal to ace their studies
          </p>
          <button
            onClick={() => handleUpgrade('premium')}
            className="bg-white text-teal-600 px-8 py-4 rounded-xl font-bold text-lg hover:shadow-lg transform hover:scale-105 transition-all"
          >
            Start Your Premium Journey - KSH 500/month
          </button>
          <p className="mt-4 text-sm opacity-80">
            🎉 First week free • Cancel anytime • 24/7 support
          </p>
        </div>
      </div>
    </div>
  );
};

export default Pricing;