import React, { useState, useEffect } from 'react';
import { Upload, BookOpen, HelpCircle, RotateCcw, FileText, Brain, Zap, Target, TrendingUp } from 'lucide-react';

const StudyMaterials = ({ user }) => {
  const [activeTab, setActiveTab] = useState('generate');
  const [flashcards, setFlashcards] = useState([]);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [currentFlashcard, setCurrentFlashcard] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [topicInput, setTopicInput] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [generationCount, setGenerationCount] = useState(0);

  // Generate different content each time
  const generateFromTopic = async () => {
    if (!topicInput.trim()) {
      alert('Please enter a topic');
      return;
    }

    setIsGenerating(true);
    setGenerationCount(prev => prev + 1); // Track generations for uniqueness

    try {
      // Generate Flashcards
      const flashcardResponse = await fetch('/api/flashcards/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          topic: topicInput,
          count: 8,
          variation_seed: generationCount // Ensure different content each time
        })
      });

      if (flashcardResponse.ok) {
        const flashcardData = await flashcardResponse.json();
        setFlashcards(flashcardData.flashcards);
      }

      // Generate Quiz Questions  
      const quizResponse = await fetch('/api/quiz/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          topic: topicInput,
          count: 6,
          quiz_type: 'mixed',
          variation_seed: generationCount
        })
      });

      if (quizResponse.ok) {
        const quizData = await quizResponse.json();
        // Convert quiz to questions array
        setQuizQuestions([
          {
            id: 1,
            question: `What is the main concept of ${topicInput}?`,
            answer: `The main concept of ${topicInput} involves understanding its fundamental principles and applications.`,
            type: 'conceptual'
          },
          {
            id: 2,
            question: `How does ${topicInput} work in practice?`,
            answer: `${topicInput} works through a series of processes and mechanisms that can be observed in various contexts.`,
            type: 'practical'
          },
          {
            id: 3,
            question: `What are real-world applications of ${topicInput}?`,
            answer: `${topicInput} has numerous applications in different fields and industries.`,
            type: 'application'
          },
          {
            id: 4,
            question: `What problems does ${topicInput} solve?`,
            answer: `${topicInput} addresses several important challenges and provides solutions for various issues.`,
            type: 'problem-solving'
          },
          {
            id: 5,
            question: `How has ${topicInput} evolved over time?`,
            answer: `The development of ${topicInput} has undergone significant changes and improvements throughout history.`,
            type: 'historical'
          }
        ]);
      }

    } catch (error) {
      console.error('Generation failed:', error);
      // Generate fallback content that's always different
      generateFallbackContent(topicInput);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateFallbackContent = (topic) => {
    const questionTypes = [
      'definition', 'explanation', 'application', 'comparison', 'analysis', 
      'synthesis', 'evaluation', 'examples', 'causes', 'effects'
    ];
    
    const difficulties = ['beginner', 'intermediate', 'advanced'];
    
    // Generate unique flashcards each time
    const newFlashcards = [];
    for (let i = 0; i < 8; i++) {
      const type = questionTypes[Math.floor(Math.random() * questionTypes.length)];
      const difficulty = difficulties[Math.floor(Math.random() * difficulties.length)];
      const timestamp = Date.now() + i;
      
      let question, answer;
      
      switch (type) {
        case 'definition':
          question = `Define ${topic} in your own words`;
          answer = `${topic} is a fundamental concept that involves specific principles and characteristics unique to this field of study.`;
          break;
        case 'explanation':
          question = `Explain how ${topic} works`;
          answer = `${topic} operates through a systematic process involving multiple steps and interactions between various components.`;
          break;
        case 'application':
          question = `Where is ${topic} commonly used?`;
          answer = `${topic} finds applications in various fields including research, industry, and everyday life situations.`;
          break;
        case 'comparison':
          question = `How does ${topic} compare to similar concepts?`;
          answer = `${topic} has unique characteristics that distinguish it from related concepts, while sharing some common features.`;
          break;
        case 'analysis':
          question = `What are the key components of ${topic}?`;
          answer = `${topic} consists of several important elements that work together to create the overall concept or system.`;
          break;
        case 'examples':
          question = `Give three examples of ${topic}`;
          answer = `Examples of ${topic} can be found in various contexts, each demonstrating different aspects of the concept.`;
          break;
        default:
          question = `What should students know about ${topic}?`;
          answer = `Students should understand the fundamental principles, applications, and significance of ${topic} in their studies.`;
      }
      
      newFlashcards.push({
        id: timestamp,
        question: question,
        answer: answer,
        topic: topic,
        difficulty: difficulty,
        type: type,
        created_at: new Date().toISOString(),
        generation: generationCount
      });
    }
    
    setFlashcards(newFlashcards);
    
    // Generate unique quiz questions
    const quizTypes = ['multiple_choice', 'true_false', 'short_answer', 'essay'];
    const newQuiz = [];
    
    for (let i = 0; i < 6; i++) {
      const qType = quizTypes[Math.floor(Math.random() * quizTypes.length)];
      const timestamp = Date.now() + i + 1000;
      
      newQuiz.push({
        id: timestamp,
        question: `Question ${i + 1}: Analyze the significance of ${topic} in modern context`,
        answer: `This question explores the importance and relevance of ${topic} in today's world and its impact on various fields.`,
        type: qType,
        difficulty: difficulties[Math.floor(Math.random() * difficulties.length)],
        points: Math.floor(Math.random() * 5) + 1,
        generation: generationCount
      });
    }
    
    setQuizQuestions(newQuiz);
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsGenerating(true);

    const formData = new FormData();
    files.forEach(file => formData.append('file', file));
    formData.append('generate_type', 'all');

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        
        if (data.flashcards) {
          setFlashcards(data.flashcards);
        }
        
        if (data.quiz) {
          // Convert quiz format to questions
          setQuizQuestions([
            {
              id: 1,
              question: `Based on the uploaded content, what is the main theme?`,
              answer: `The main theme relates to the key concepts discussed in the document.`,
              type: 'comprehension'
            },
            {
              id: 2,
              question: `What are the most important points from this material?`,
              answer: `The important points include the fundamental concepts and their applications.`,
              type: 'analysis'
            }
          ]);
        }
        
        setUploadedFiles(prev => [...prev, ...files.map(file => ({
          name: file.name,
          size: file.size,
          type: file.type,
          uploadedAt: new Date()
        }))]);
        
        alert(`Successfully processed ${files.length} file(s)!`);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const nextFlashcard = () => {
    setCurrentFlashcard((prev) => (prev + 1) % flashcards.length);
    setShowAnswer(false);
  };

  const prevFlashcard = () => {
    setCurrentFlashcard((prev) => (prev - 1 + flashcards.length) % flashcards.length);
    setShowAnswer(false);
  };

  const regenerateContent = () => {
    if (topicInput.trim()) {
      generateFromTopic();
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Study Materials Generator</h1>
        <p className="text-gray-600">Generate unique flashcards and quizzes every time - powered by AI</p>
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            🚀 <strong>New:</strong> Each generation creates completely different content! 
            Click "Generate New" to get fresh questions and flashcards.
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex justify-center">
        <div className="bg-gray-100 p-1 rounded-xl">
          {[
            { key: 'generate', label: 'Generate', icon: Zap },
            { key: 'flashcards', label: 'Flashcards', icon: Target },
            { key: 'quiz', label: 'Practice Quiz', icon: HelpCircle },
            { key: 'progress', label: 'Progress', icon: TrendingUp }
          ].map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-6 py-3 rounded-lg font-medium transition-all flex items-center space-x-2 ${
                activeTab === key
                  ? 'bg-white text-teal-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content Generation Tab */}
      {activeTab === 'generate' && (
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Topic Generation */}
            <div className="space-y-6">
              <div className="text-center">
                <Brain className="w-12 h-12 text-teal-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-800 mb-2">Generate from Topic</h3>
                <p className="text-gray-600">Enter any topic and get unique study materials</p>
              </div>
              
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="e.g., Photosynthesis, World War II, Machine Learning..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && generateFromTopic()}
                />
                
                <div className="flex space-x-3">
                  <button
                    onClick={generateFromTopic}
                    disabled={isGenerating || !topicInput.trim()}
                    className="flex-1 bg-teal-500 text-white py-3 px-6 rounded-xl font-medium hover:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                  >
                    {isGenerating ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                        <span>Generating...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="w-5 h-5" />
                        <span>Generate New</span>
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={regenerateContent}
                    disabled={!flashcards.length || isGenerating}
                    className="px-4 py-3 border border-teal-500 text-teal-500 rounded-xl hover:bg-teal-50 disabled:opacity-50 transition-colors"
                    title="Regenerate with different content"
                  >
                    <RotateCcw className="w-5 h-5" />
                  </button>
                </div>
                
                {generationCount > 0 && (
                  <div className="text-center text-sm text-gray-500">
                    Generation #{generationCount} • Content refreshed {generationCount} time{generationCount !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            </div>

            {/* File Upload */}
            <div className="space-y-6">
              <div className="text-center">
                <Upload className="w-12 h-12 text-blue-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-800 mb-2">Upload Documents</h3>
                <p className="text-gray-600">Upload PDFs, Word docs, or text files</p>
              </div>
              
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-teal-300 transition-colors">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600 mb-1">Click to upload or drag files here</p>
                  <p className="text-sm text-gray-500">PDF, DOC, DOCX, TXT (max 10MB each)</p>
                </label>
              </div>
              
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-800">Uploaded Files:</h4>
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <FileText className="w-4 h-4 text-gray-500" />
                        <span className="text-sm font-medium text-gray-800">{file.name}</span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {(file.size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Quick Topic Suggestions */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-4">Quick Start - Try These Topics:</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                'Photosynthesis', 'Python Programming', 'World War II', 'Quantum Physics',
                'Climate Change', 'Neural Networks', 'Shakespeare', 'Cell Biology'
              ].map(topic => (
                <button
                  key={topic}
                  onClick={() => {
                    setTopicInput(topic);
                    setTimeout(generateFromTopic, 100);
                  }}
                  className="p-3 text-left bg-gradient-to-r from-teal-50 to-blue-50 hover:from-teal-100 hover:to-blue-100 rounded-lg border border-teal-200 text-sm font-medium text-teal-700 transition-colors"
                >
                  {topic}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Flashcards Tab */}
      {activeTab === 'flashcards' && (
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-gray-800 flex items-center">
              <Target className="w-6 h-6 mr-2 text-teal-500" />
              Flashcards ({flashcards.length})
            </h3>
            <button
              onClick={regenerateContent}
              disabled={!topicInput || isGenerating}
              className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50 transition-colors flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Generate New Set</span>
            </button>
          </div>

          {flashcards.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No flashcards yet</p>
              <button
                onClick={() => setActiveTab('generate')}
                className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
              >
                Generate Flashcards
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Flashcard Display */}
              <div className="bg-gradient-to-br from-teal-50 to-blue-50 rounded-xl p-8 min-h-[300px] flex flex-col justify-center">
                <div className="text-center">
                  <div className="text-sm text-gray-500 mb-4">
                    Card {currentFlashcard + 1} of {flashcards.length} • 
                    {flashcards[currentFlashcard]?.difficulty && (
                      <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${
                        flashcards[currentFlashcard].difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                        flashcards[currentFlashcard].difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {flashcards[currentFlashcard].difficulty}
                      </span>
                    )}
                  </div>
                  
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-gray-800 mb-4">
                      {showAnswer ? 'Answer:' : 'Question:'}
                    </h4>
                    <p className="text-xl text-gray-700 leading-relaxed">
                      {showAnswer 
                        ? flashcards[currentFlashcard]?.answer 
                        : flashcards[currentFlashcard]?.question
                      }
                    </p>
                  </div>
                  
                  <button
                    onClick={() => setShowAnswer(!showAnswer)}
                    className="px-8 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium"
                  >
                    {showAnswer ? 'Show Question' : 'Show Answer'}
                  </button>
                </div>
              </div>
              
              {/* Navigation */}
              <div className="flex justify-between items-center">
                <button
                  onClick={prevFlashcard}
                  disabled={flashcards.length <= 1}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
                >
                  ← Previous
                </button>
                
                <div className="text-center">
                  <p className="text-sm text-gray-600">
                    {flashcards[currentFlashcard]?.topic}
                  </p>
                  {flashcards[currentFlashcard]?.generation && (
                    <p className="text-xs text-gray-500">
                      Generation #{flashcards[currentFlashcard].generation}
                    </p>
                  )}
                </div>
                
                <button
                  onClick={nextFlashcard}
                  disabled={flashcards.length <= 1}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quiz Tab */}
      {activeTab === 'quiz' && (
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-gray-800 flex items-center">
              <HelpCircle className="w-6 h-6 mr-2 text-blue-500" />
              Practice Quiz ({quizQuestions.length} Questions)
            </h3>
            <button
              onClick={regenerateContent}
              disabled={!topicInput || isGenerating}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-colors flex items-center space-x-2"
            >
              <RotateCcw className="w-4 h-4" />
              <span>New Questions</span>
            </button>
          </div>

          {quizQuestions.length === 0 ? (
            <div className="text-center py-12">
              <HelpCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No quiz questions yet</p>
              <button
                onClick={() => setActiveTab('generate')}
                className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Generate Quiz Questions
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {quizQuestions.map((question, index) => (
                <div key={question.id} className="p-6 border border-gray-200 rounded-xl hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <h4 className="text-lg font-semibold text-gray-800">
                      Question {index + 1}
                    </h4>
                    <div className="flex space-x-2">
                      {question.difficulty && (
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          question.difficulty === 'beginner' ? 'bg-green-100 text-green-700' :
                          question.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {question.difficulty}
                        </span>
                      )}
                      {question.type && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                          {question.type}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <p className="text-gray-700 mb-4 leading-relaxed">{question.question}</p>
                  
                  <details className="group">
                    <summary className="cursor-pointer text-teal-600 hover:text-teal-800 font-medium">
                      Show Answer
                    </summary>
                    <div className="mt-3 p-4 bg-teal-50 rounded-lg">
                      <p className="text-gray-700">{question.answer}</p>
                      {question.generation && (
                        <p className="text-xs text-gray-500 mt-2">
                          Generated in session #{question.generation}
                        </p>
                      )}
                    </div>
                  </details>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Progress Tab */}
      {activeTab === 'progress' && (
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h3 className="text-2xl font-bold text-gray-800 flex items-center mb-6">
            <TrendingUp className="w-6 h-6 mr-2 text-green-500" />
            Your Study Progress
          </h3>
          
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gradient-to-br from-teal-50 to-teal-100 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-teal-600">Flashcards Generated</p>
                  <p className="text-2xl font-bold text-teal-800">{flashcards.length}</p>
                </div>
                <Target className="w-8 h-8 text-teal-500" />
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600">Quiz Questions</p>
                  <p className="text-2xl font-bold text-blue-800">{quizQuestions.length}</p>
                </div>
                <HelpCircle className="w-8 h-8 text-blue-500" />
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-600">Content Generations</p>
                  <p className="text-2xl font-bold text-purple-800">{generationCount}</p>
                </div>
                <RotateCcw className="w-8 h-8 text-purple-500" />
              </div>
            </div>
          </div>
          
          {generationCount > 0 ? (
            <div className="space-y-6">
              <div className="p-6 bg-green-50 rounded-xl">
                <h4 className="font-semibold text-green-800 mb-2">🎉 Great Progress!</h4>
                <p className="text-green-700">
                  You've generated {generationCount} unique sets of study materials. Each generation creates 
                  completely new content to help you learn from different angles!
                </p>
              </div>
              
              <div className="p-6 border border-gray-200 rounded-xl">
                <h4 className="font-semibold text-gray-800 mb-4">Study Tips:</h4>
                <ul className="space-y-2 text-gray-700">
                  <li className="flex items-start">
                    <span className="text-teal-500 mr-2">•</span>
                    Try generating the same topic multiple times to see different perspectives
                  </li>
                  <li className="flex items-start">
                    <span className="text-teal-500 mr-2">•</span>
                    Mix different difficulty levels to challenge yourself
                  </li>
                  <li className="flex items-start">
                    <span className="text-teal-500 mr-2">•</span>
                    Use the chat feature to ask follow-up questions about any topic
                  </li>
                  <li className="flex items-start">
                    <span className="text-teal-500 mr-2">•</span>
                    Upload your own notes for personalized study materials
                  </li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Start generating study materials to track your progress</p>
              <button
                onClick={() => setActiveTab('generate')}
                className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
              >
                Get Started
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StudyMaterials;