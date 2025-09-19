import os
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from transformers import pipeline, AutoTokenizer, AutoModel
from huggingface_hub import HfApi, InferenceClient
import requests

load_dotenv()

# Initialize Hugging Face
hf_token = os.getenv("HUGGINGFACE_API_KEY")
client = InferenceClient(token=hf_token) if hf_token else None

# Global pipelines for reuse
qa_pipeline = None
generator_pipeline = None
summarizer_pipeline = None

def get_qa_pipeline():
    """Lazy loading of QA pipeline"""
    global qa_pipeline
    if qa_pipeline is None:
        qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
    return qa_pipeline

def get_generator_pipeline():
    """Lazy loading of text generation pipeline"""
    global generator_pipeline
    if generator_pipeline is None:
        generator_pipeline = pipeline('text-generation', model='gpt2')
    return generator_pipeline

def get_summarizer_pipeline():
    """Lazy loading of summarization pipeline"""
    global summarizer_pipeline
    if summarizer_pipeline is None:
        summarizer_pipeline = pipeline("summarization", model="facebook/bart-large-cnn")
    return summarizer_pipeline

def answer_any_question(question, context=""):
    """Answer ANY question from user - complete freedom"""
    try:
        # If context is provided, use QA model
        if context and len(context) > 50:
            qa_model = get_qa_pipeline()
            result = qa_model(question=question, context=context)
            return {
                "answer": result['answer'],
                "confidence": result.get('score', 0),
                "source": "context_based"
            }
        
        # For general questions, use Hugging Face API
        if client:
            response = client.text_generation(
                f"Question: {question}\n\nProvide a detailed educational answer:\n",
                model="microsoft/DialoGPT-medium",
                max_new_tokens=200,
                temperature=0.8
            )
            return {
                "answer": response,
                "source": "huggingface_api"
            }
        
        # Fallback to local generation
        generator = get_generator_pipeline()
        prompt = f"Q: {question}\nA: Let me explain this clearly:"
        result = generator(prompt, max_length=150, num_return_sequences=1, pad_token_id=50256)
        
        full_text = result[0]['generated_text']
        if "A:" in full_text:
            answer = full_text.split("A:")[-1].strip()
        else:
            answer = full_text
            
        return {
            "answer": answer,
            "source": "local_generation"
        }
        
    except Exception as e:
        return {
            "answer": f"I'm having trouble answering that question. Could you try rephrasing it?",
            "error": str(e),
            "source": "error"
        }

def generate_dynamic_flashcards(content, topic="", count=5):
    """Generate different flashcards each time with variety"""
    
    # Different question templates for variety
    question_templates = [
        # Basic understanding
        ["What is {topic}?", "Define {topic}?", "Explain {topic} in simple terms"],
        ["What are the main components of {topic}?", "What elements make up {topic}?", "List the key parts of {topic}"],
        ["How does {topic} work?", "Explain the process of {topic}", "Describe how {topic} functions"],
        
        # Application/examples
        ["Give an example of {topic}", "Where do we see {topic} in real life?", "How is {topic} used?"],
        ["What are the benefits of {topic}?", "Why is {topic} important?", "What advantages does {topic} provide?"],
        
        # Analysis
        ["What happens if {topic} fails?", "What are the consequences of {topic}?", "What problems does {topic} solve?"],
        ["Compare {topic} with similar concepts", "How is {topic} different from alternatives?", "What makes {topic} unique?"],
        
        # Memory aids
        ["What's the easiest way to remember {topic}?", "Create a mnemonic for {topic}", "What's a simple way to explain {topic}?"]
    ]
    
    try:
        qa_model = get_qa_pipeline()
        flashcards = []
        
        # Randomly select question types for variety
        selected_templates = random.sample(question_templates, min(count, len(question_templates)))
        
        for template_group in selected_templates:
            # Pick random question from each group
            question_template = random.choice(template_group)
            
            # Format with topic if provided
            if topic and "{topic}" in question_template:
                question = question_template.replace("{topic}", topic)
            else:
                # Generate contextual question
                question = question_template.replace("{topic}", "this concept")
            
            try:
                # Try to answer using the content
                answer_result = qa_model(question=question, context=content)
                
                flashcards.append({
                    "id": f"fc_{datetime.now().timestamp()}_{random.randint(1000,9999)}",
                    "question": question,
                    "answer": answer_result['answer'],
                    "confidence": answer_result.get('score', 0),
                    "topic": topic,
                    "created_at": datetime.now().isoformat(),
                    "difficulty": "intermediate" if answer_result.get('score', 0) > 0.5 else "beginner"
                })
            except:
                # Fallback answer generation
                fallback_answer = f"This relates to the key concepts in {topic or 'the material'}"
                flashcards.append({
                    "id": f"fc_{datetime.now().timestamp()}_{random.randint(1000,9999)}",
                    "question": question,
                    "answer": fallback_answer,
                    "confidence": 0.3,
                    "topic": topic,
                    "created_at": datetime.now().isoformat(),
                    "difficulty": "beginner"
                })
        
        return flashcards
        
    except Exception as e:
        return {"error": f"Flashcard generation failed: {str(e)}"}

def generate_dynamic_quiz(content, topic="", count=5, quiz_type="mixed"):
    """Generate different quiz questions each time"""
    
    quiz_templates = {
        "multiple_choice": [
            "What is the primary function of {concept}?",
            "Which of the following best describes {concept}?",
            "What happens when {concept} occurs?"
        ],
        "true_false": [
            "{concept} is essential for the process",
            "The main purpose of {concept} is to provide energy",
            "{concept} can occur without external factors"
        ],
        "short_answer": [
            "Explain how {concept} works in your own words",
            "Give an example of {concept} in nature",
            "What would happen if {concept} didn't exist?"
        ],
        "fill_blank": [
            "The process of {concept} involves _____ and _____",
            "{concept} occurs when _____ meets _____",
            "The main result of {concept} is _____"
        ]
    }
    
    try:
        quiz_questions = []
        qa_model = get_qa_pipeline()
        
        # Mix different question types
        if quiz_type == "mixed":
            types_to_use = list(quiz_templates.keys())
        else:
            types_to_use = [quiz_type] if quiz_type in quiz_templates else ["short_answer"]
        
        for i in range(count):
            question_type = random.choice(types_to_use)
            template = random.choice(quiz_templates[question_type])
            
            # Extract key concepts from content for template
            key_concepts = extract_key_concepts(content, topic)
            concept = random.choice(key_concepts) if key_concepts else (topic or "this concept")
            
            question = template.replace("{concept}", concept)
            
            # Generate answer based on content
            try:
                if question_type == "multiple_choice":
                    # Generate answer and distractors
                    answer_result = qa_model(question=question, context=content)
                    correct_answer = answer_result['answer']
                    
                    quiz_questions.append({
                        "id": f"quiz_{datetime.now().timestamp()}_{random.randint(1000,9999)}",
                        "question": question,
                        "type": "multiple_choice",
                        "options": [
                            correct_answer,
                            f"Alternative explanation of {concept}",
                            f"Different aspect of {concept}",
                            f"Unrelated to {concept}"
                        ],
                        "correct_answer": 0,  # First option is correct
                        "explanation": f"The correct answer is: {correct_answer}",
                        "topic": topic,
                        "difficulty": "intermediate",
                        "created_at": datetime.now().isoformat()
                    })
                
                elif question_type == "true_false":
                    # Generate true/false with explanation
                    is_true = random.choice([True, False])
                    quiz_questions.append({
                        "id": f"quiz_{datetime.now().timestamp()}_{random.randint(1000,9999)}",
                        "question": question,
                        "type": "true_false",
                        "correct_answer": is_true,
                        "explanation": f"This statement is {'true' if is_true else 'false'} based on the content",
                        "topic": topic,
                        "difficulty": "beginner",
                        "created_at": datetime.now().isoformat()
                    })
                
                else:  # short_answer, fill_blank
                    answer_result = qa_model(question=question, context=content)
                    quiz_questions.append({
                        "id": f"quiz_{datetime.now().timestamp()}_{random.randint(1000,9999)}",
                        "question": question,
                        "type": question_type,
                        "answer": answer_result['answer'],
                        "topic": topic,
                        "difficulty": "advanced",
                        "created_at": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                # Fallback question
                quiz_questions.append({
                    "id": f"quiz_{datetime.now().timestamp()}_{random.randint(1000,9999)}",
                    "question": f"Explain the main concept of {concept}",
                    "type": "short_answer",
                    "answer": f"This question relates to {concept} in the context of {topic}",
                    "topic": topic,
                    "difficulty": "beginner",
                    "created_at": datetime.now().isoformat()
                })
        
        return quiz_questions
        
    except Exception as e:
        return {"error": f"Quiz generation failed: {str(e)}"}

def generate_practice_questions(topic, difficulty="mixed", count=10):
    """Generate practice questions just from topic name"""
    
    difficulty_prompts = {
        "beginner": f"Generate basic questions about {topic} for beginners",
        "intermediate": f"Create intermediate level questions about {topic}",
        "advanced": f"Generate advanced questions about {topic} for experts",
        "mixed": f"Create questions of varying difficulty about {topic}"
    }
    
    question_types = [
        f"What is {topic} and why is it important?",
        f"How does {topic} work in simple terms?",
        f"Give three real-world examples of {topic}",
        f"What are the main benefits of understanding {topic}?",
        f"How would you explain {topic} to a 10-year-old?",
        f"What problems does {topic} solve?",
        f"Compare {topic} with similar concepts",
        f"What happens when {topic} goes wrong?",
        f"What are the future applications of {topic}?",
        f"How has {topic} evolved over time?"
    ]
    
    try:
        practice_questions = []
        
        # Generate varied questions
        selected_questions = random.sample(question_types, min(count, len(question_types)))
        
        for i, question_template in enumerate(selected_questions):
            # Add some variation to each question
            variations = [
                question_template,
                question_template.replace("What", "How"),
                question_template.replace("How", "Why"),
            ]
            
            final_question = random.choice(variations)
            
            # Generate answer using AI
            answer_data = answer_any_question(final_question)
            
            practice_questions.append({
                "id": f"practice_{datetime.now().timestamp()}_{i}",
                "question": final_question,
                "answer": answer_data.get('answer', 'Answer will be provided based on your response'),
                "topic": topic,
                "difficulty": random.choice(["beginner", "intermediate", "advanced"]) if difficulty == "mixed" else difficulty,
                "type": "practice",
                "created_at": datetime.now().isoformat(),
                "confidence": answer_data.get('confidence', 0.7)
            })
        
        return practice_questions
        
    except Exception as e:
        return {"error": f"Practice question generation failed: {str(e)}"}

def extract_key_concepts(text, topic=""):
    """Extract key concepts from text for question generation"""
    try:
        # Simple keyword extraction
        words = text.lower().split()
        
        # Common educational keywords to look for
        important_words = []
        for word in words:
            if len(word) > 4 and word not in ['this', 'that', 'with', 'from', 'they', 'have', 'will', 'been', 'there', 'their']:
                important_words.append(word)
        
        # Get most frequent words
        from collections import Counter
        concept_counts = Counter(important_words)
        top_concepts = [word for word, count in concept_counts.most_common(5)]
        
        # Add topic if provided
        if topic:
            top_concepts.insert(0, topic.lower())
        
        return top_concepts[:5]
        
    except:
        return [topic.lower()] if topic else ["the concept"]

def process_uploaded_file(file_content, filename="", generate_type="all"):
    """Process uploaded files and generate study materials"""
    try:
        # Extract topic from filename if possible
        topic = filename.replace('.pdf', '').replace('.txt', '').replace('.docx', '').replace('_', ' ')
        
        results = {}
        
        if generate_type in ["all", "flashcards"]:
            results["flashcards"] = generate_dynamic_flashcards(file_content, topic, count=8)
        
        if generate_type in ["all", "quiz"]:
            results["quiz"] = generate_dynamic_quiz(file_content, topic, count=6)
        
        if generate_type in ["all", "summary"]:
            summarizer = get_summarizer_pipeline()
            summary = summarizer(file_content[:1000], max_length=150, min_length=50)
            results["summary"] = {
                "text": summary[0]['summary_text'],
                "created_at": datetime.now().isoformat()
            }
        
        return results
        
    except Exception as e:
        return {"error": f"File processing failed: {str(e)}"}

def chat_with_user(message, conversation_history=[]):
    """Handle chat conversations with memory"""
    try:
        # Build context from conversation history
        context = ""
        if conversation_history:
            for msg in conversation_history[-3:]:  # Last 3 messages for context
                context += f"User: {msg.get('user', '')}\nAI: {msg.get('ai', '')}\n"
        
        # Generate response
        if client:
            full_prompt = f"{context}User: {message}\nAI: Let me help you with that."
            response = client.text_generation(
                full_prompt,
                model="microsoft/DialoGPT-medium",
                max_new_tokens=200,
                temperature=0.8
            )
        else:
            # Fallback to local generation
            response_data = answer_any_question(message)
            response = response_data.get('answer', 'I can help you with that question.')
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "context_used": bool(conversation_history)
        }
        
    except Exception as e:
        return {
            "response": "I'm having trouble right now. Could you try asking again?",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Main interface functions
def handle_user_request(request_type, content="", topic="", options={}):
    """
    Main handler for all AI requests
    
    request_type: 'chat', 'flashcards', 'quiz', 'practice', 'file_upload'
    content: user message, file content, or topic
    topic: subject matter
    options: additional parameters
    """
    
    if request_type == "chat":
        history = options.get('history', [])
        return chat_with_user(content, history)
    
    elif request_type == "flashcards":
        if content:  # From uploaded content
            return generate_dynamic_flashcards(content, topic, options.get('count', 5))
        else:  # From topic only
            practice_q = generate_practice_questions(topic, count=5)
            # Convert practice questions to flashcard format
            flashcards = []
            for q in practice_q:
                flashcards.append({
                    "id": q['id'],
                    "question": q['question'],
                    "answer": q['answer'],
                    "topic": q['topic'],
                    "difficulty": q['difficulty'],
                    "created_at": q['created_at']
                })
            return flashcards
    
    elif request_type == "quiz":
        if content:
            return generate_dynamic_quiz(content, topic, options.get('count', 5))
        else:
            return generate_practice_questions(topic, count=options.get('count', 5))
    
    elif request_type == "practice":
        return generate_practice_questions(topic, options.get('difficulty', 'mixed'), options.get('count', 10))
    
    elif request_type == "file_upload":
        return process_uploaded_file(content, options.get('filename', ''), options.get('generate_type', 'all'))
    
    else:
        return {"error": "Unknown request type"}