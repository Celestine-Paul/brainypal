import os
import time
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import json

# Import our custom modules
from ai_service import handle_user_request, answer_any_question
from models import (
    db, User, Conversation, Message, Flashcard, Quiz, QuizQuestion, 
    StudySession, UploadedFile, UserProgress,
    create_conversation, add_message, save_flashcards, save_quiz,
    get_user_conversations, get_conversation_messages, get_user_flashcards,
    update_flashcard_performance, save_study_session, update_user_progress
)

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///brainypal.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-for-sessions')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
cors = CORS(app)
jwt = JWTManager(app)

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath, filename):
    """Extract text from uploaded files"""
    try:
        if filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        elif filename.endswith('.pdf'):
            # For now, return placeholder - in production use PyPDF2 or similar
            return "PDF content extraction - implement with PyPDF2 or pdfplumber"
        elif filename.endswith(('.doc', '.docx')):
            # For now, return placeholder - in production use python-docx
            return "Word document content - implement with python-docx"
        else:
            return "Unsupported file type"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "BrainyPal Backend is running!",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Authentication Routes
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 409
        
        # Create user
        password_hash = generate_password_hash(password)
        user = User(email=email, password_hash=password_hash)
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Create first conversation
        conversation = create_conversation(user.id, "Welcome Chat")
        
        return jsonify({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat()
            },
            "access_token": access_token,
            "conversation_id": conversation.id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Update last active
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "last_active": user.last_active.isoformat()
            },
            "access_token": access_token
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Chat and AI Routes
@app.route('/api/chat/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """Get user's conversation history"""
    try:
        user_id = get_jwt_identity()
        conversations = get_user_conversations(user_id)
        
        conversations_data = []
        for conv in conversations:
            # Get last message for preview
            last_message = Message.query.filter_by(conversation_id=conv.id)\
                .order_by(Message.timestamp.desc()).first()
            
            conversations_data.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else (last_message.content if last_message else ""),
                "message_count": len(conv.messages)
            })
        
        return jsonify({
            "conversations": conversations_data,
            "total": len(conversations_data)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/conversation/<int:conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation_detail(conversation_id):
    """Get specific conversation with all messages"""
    try:
        user_id = get_jwt_identity()
        
        # Verify ownership
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            return jsonify({"error": "Conversation not found"}), 404
        
        messages = get_conversation_messages(conversation_id)
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                "id": msg.id,
                "content": msg.content,
                "is_user": msg.is_user,
                "timestamp": msg.timestamp.isoformat(),
                "ai_model": msg.ai_model,
                "confidence": msg.confidence
            })
        
        return jsonify({
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat()
            },
            "messages": messages_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/send', methods=['POST'])
@jwt_required()
def send_chat_message():
    """Send a chat message and get AI response"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        message_content = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not message_content:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Create new conversation if not provided
        if not conversation_id:
            conversation = create_conversation(user_id, message_content[:50] + "..." if len(message_content) > 50 else message_content)
            conversation_id = conversation.id
        else:
            # Verify ownership
            conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
            if not conversation:
                return jsonify({"error": "Conversation not found"}), 404
        
        # Save user message
        start_time = time.time()
        user_message = add_message(conversation_id, message_content, is_user=True)
        
        # Get conversation history for context
        recent_messages = Message.query.filter_by(conversation_id=conversation_id)\
            .order_by(Message.timestamp.desc()).limit(6).all()
        
        history = []
        for msg in reversed(recent_messages[:-1]):  # Exclude the message we just added
            history.append({
                "user" if msg.is_user else "ai": msg.content
            })
        
        # Generate AI response
        ai_response_data = handle_user_request(
            request_type="chat",
            content=message_content,
            options={"history": history}
        )
        
        processing_time = time.time() - start_time
        
        # Extract response text
        if isinstance(ai_response_data, dict):
            ai_response = ai_response_data.get('response', 'I apologize, but I cannot provide a response right now.')
            confidence = ai_response_data.get('confidence', 0.7)
        else:
            ai_response = str(ai_response_data)
            confidence = 0.7
        
        # Save AI response
        ai_message = add_message(
            conversation_id, 
            ai_response, 
            is_user=False,
            ai_model="huggingface",
            confidence=confidence,
            processing_time=processing_time
        )
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "user_message": {
                "id": user_message.id,
                "content": user_message.content,
                "timestamp": user_message.timestamp.isoformat()
            },
            "ai_response": {
                "id": ai_message.id,
                "content": ai_message.content,
                "timestamp": ai_message.timestamp.isoformat(),
                "confidence": confidence,
                "processing_time": processing_time
            },
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# File Upload and Processing
@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload and process files for study material generation"""
    try:
        user_id = get_jwt_identity()
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{user_id}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(filepath)
        
        # Extract text content
        content = extract_text_from_file(filepath, filename)
        
        # Save file record
        uploaded_file = UploadedFile(
            user_id=user_id,
            filename=unique_filename,
            original_filename=filename,
            file_type=filename.rsplit('.', 1)[1].lower(),
            file_size=os.path.getsize(filepath),
            content=content,
            processed=True,
            processed_at=datetime.utcnow()
        )
        
        db.session.add(uploaded_file)
        db.session.flush()
        
        # Generate study materials
        generate_type = request.form.get('generate_type', 'all')
        ai_results = handle_user_request(
            request_type="file_upload",
            content=content,
            options={
                "filename": filename,
                "generate_type": generate_type
            }
        )
        
        response_data = {
            "file": {
                "id": uploaded_file.id,
                "filename": filename,
                "size": uploaded_file.file_size,
                "type": uploaded_file.file_type,
                "uploaded_at": uploaded_file.uploaded_at.isoformat()
            }
        }
        
        # Save generated content
        if isinstance(ai_results, dict):
            if 'flashcards' in ai_results:
                flashcards = save_flashcards(
                    user_id, 
                    ai_results['flashcards'], 
                    source_type="uploaded_file",
                    source_content=content
                )
                uploaded_file.flashcards_generated = len(flashcards)
                response_data['flashcards'] = [
                    {
                        "id": fc.id,
                        "question": fc.question,
                        "answer": fc.answer,
                        "topic": fc.topic,
                        "difficulty": fc.difficulty
                    } for fc in flashcards
                ]
            
            if 'quiz' in ai_results:
                quiz = save_quiz(
                    user_id,
                    {
                        "title": f"Quiz from {filename}",
                        "topic": filename.replace('.pdf', '').replace('.txt', ''),
                        "source_type": "uploaded_file",
                        "source_content": content
                    },
                    ai_results['quiz']
                )
                uploaded_file.quiz_questions_generated = len(ai_results['quiz'])
                response_data['quiz'] = {
                    "id": quiz.id,
                    "title": quiz.title,
                    "questions_count": quiz.total_questions
                }
            
            if 'summary' in ai_results:
                uploaded_file.content_summary = ai_results['summary']['text']
                response_data['summary'] = ai_results['summary']['text']
        
        db.session.commit()
        
        # Clean up file (optional - you might want to keep files)
        # os.remove(filepath)
        
        return jsonify(response_data), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Study Material Routes
@app.route('/api/flashcards', methods=['GET'])
@jwt_required()
def get_flashcards():
    """Get user's flashcards"""
    try:
        user_id = get_jwt_identity()
        topic = request.args.get('topic')
        
        flashcards = get_user_flashcards(user_id, topic)
        
        flashcards_data = []
        for fc in flashcards:
            flashcards_data.append({
                "id": fc.id,
                "question": fc.question,
                "answer": fc.answer,
                "topic": fc.topic,
                "difficulty": fc.difficulty,
                "times_reviewed": fc.times_reviewed,
                "times_correct": fc.times_correct,
                "mastery_level": fc.mastery_level,
                "last_reviewed": fc.last_reviewed.isoformat() if fc.last_reviewed else None,
                "created_at": fc.created_at.isoformat()
            })
        
        return jsonify({
            "flashcards": flashcards_data,
            "total": len(flashcards_data),
            "filtered_by_topic": topic
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/flashcards/generate', methods=['POST'])
@jwt_required()
def generate_flashcards():
    """Generate new flashcards from topic or content"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        topic = data.get('topic', '').strip()
        content = data.get('content', '').strip()
        count = data.get('count', 5)
        
        if not topic and not content:
            return jsonify({"error": "Topic or content required"}), 400
        
        # Generate flashcards
        ai_results = handle_user_request(
            request_type="flashcards",
            content=content,
            topic=topic,
            options={"count": count}
        )
        
        if isinstance(ai_results, dict) and 'error' in ai_results:
            return jsonify(ai_results), 500
        
        # Save flashcards
        flashcards = save_flashcards(
            user_id,
            ai_results,
            source_type="topic_generation" if not content else "content_generation",
            source_content=content or topic
        )
        
        # Update user progress
        update_user_progress(user_id, topic or "General", {
            "flashcards_reviewed": len(flashcards),
            "time_spent": 60  # Assume 1 minute per generation
        })
        
        flashcards_data = [
            {
                "id": fc.id,
                "question": fc.question,
                "answer": fc.answer,
                "topic": fc.topic,
                "difficulty": fc.difficulty,
                "created_at": fc.created_at.isoformat()
            } for fc in flashcards
        ]
        
        return jsonify({
            "flashcards": flashcards_data,
            "count": len(flashcards_data)
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/flashcards/<int:flashcard_id>/review', methods=['POST'])
@jwt_required()
def review_flashcard(flashcard_id):
    """Mark flashcard as reviewed with performance data"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        correct = data.get('correct', False)
        time_spent = data.get('time_spent', 0)
        
        # Verify ownership and update performance
        flashcard = Flashcard.query.filter_by(id=flashcard_id, user_id=user_id).first()
        if not flashcard:
            return jsonify({"error": "Flashcard not found"}), 404
        
        updated_flashcard = update_flashcard_performance(flashcard_id, correct)
        
        # Update user progress
        update_user_progress(user_id, flashcard.topic, {
            "flashcards_reviewed": 1,
            "time_spent": time_spent,
            "score": 100 if correct else 0
        })
        
        return jsonify({
            "flashcard": {
                "id": updated_flashcard.id,
                "times_reviewed": updated_flashcard.times_reviewed,
                "times_correct": updated_flashcard.times_correct,
                "mastery_level": updated_flashcard.mastery_level,
                "last_reviewed": updated_flashcard.last_reviewed.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quiz/generate', methods=['POST'])
@jwt_required()
def generate_quiz():
    """Generate a new quiz"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        topic = data.get('topic', '').strip()
        content = data.get('content', '').strip()
        count = data.get('count', 5)
        difficulty = data.get('difficulty', 'mixed')
        quiz_type = data.get('quiz_type', 'mixed')
        
        if not topic and not content:
            return jsonify({"error": "Topic or content required"}), 400
        
        # Generate quiz questions
        ai_results = handle_user_request(
            request_type="quiz",
            content=content,
            topic=topic,
            options={
                "count": count,
                "difficulty": difficulty,
                "quiz_type": quiz_type
            }
        )
        
        if isinstance(ai_results, dict) and 'error' in ai_results:
            return jsonify(ai_results), 500
        
        # Save quiz
        quiz = save_quiz(
            user_id,
            {
                "title": f"Quiz: {topic}" if topic else "Generated Quiz",
                "topic": topic,
                "difficulty": difficulty,
                "source_type": "topic_generation" if not content else "content_generation",
                "source_content": content or topic
            },
            ai_results
        )
        
        return jsonify({
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "topic": quiz.topic,
                "difficulty": quiz.difficulty,
                "total_questions": quiz.total_questions,
                "created_at": quiz.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/practice', methods=['POST'])
@jwt_required()
def generate_practice_questions():
    """Generate practice questions from topic"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'mixed')
        count = data.get('count', 10)
        
        if not topic:
            return jsonify({"error": "Topic required"}), 400
        
        # Generate practice questions
        ai_results = handle_user_request(
            request_type="practice",
            topic=topic,
            options={
                "difficulty": difficulty,
                "count": count
            }
        )
        
        if isinstance(ai_results, dict) and 'error' in ai_results:
            return jsonify(ai_results), 500
        
        return jsonify({
            "practice_questions": ai_results,
            "topic": topic,
            "count": len(ai_results) if isinstance(ai_results, list) else 1
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# User Progress and Analytics
@app.route('/api/progress', methods=['GET'])
@jwt_required()
def get_user_progress():
    """Get user's learning progress"""
    try:
        user_id = get_jwt_identity()
        
        # Get overall progress
        progress_records = UserProgress.query.filter_by(user_id=user_id).all()
        
        # Get recent study sessions
        recent_sessions = StudySession.query.filter_by(user_id=user_id)\
            .order_by(StudySession.started_at.desc()).limit(10).all()
        
        # Calculate overall stats
        total_study_time = sum(p.total_study_time for p in progress_records)
        total_flashcards = sum(p.flashcards_reviewed for p in progress_records)
        total_quizzes = sum(p.quizzes_completed for p in progress_records)
        avg_score = sum(p.average_score for p in progress_records) / len(progress_records) if progress_records else 0
        
        # Get topic breakdown
        topic_progress = []
        for progress in progress_records:
            topic_progress.append({
                "topic": progress.topic,
                "mastery_level": progress.mastery_level,
                "study_time": progress.total_study_time,
                "flashcards_reviewed": progress.flashcards_reviewed,
                "quizzes_completed": progress.quizzes_completed,
                "average_score": progress.average_score,
                "streak_days": progress.streak_days,
                "last_studied": progress.last_studied.isoformat() if progress.last_studied else None
            })
        
        # Recent activity
        recent_activity = []
        for session in recent_sessions:
            recent_activity.append({
                "id": session.id,
                "type": session.session_type,
                "topic": session.topic,
                "items_studied": session.items_studied,
                "accuracy": session.accuracy,
                "time_spent": session.time_spent,
                "started_at": session.started_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None
            })
        
        return jsonify({
            "overall_stats": {
                "total_study_time": total_study_time,
                "total_flashcards_reviewed": total_flashcards,
                "total_quizzes_completed": total_quizzes,
                "average_score": round(avg_score, 2),
                "topics_studied": len(progress_records)
            },
            "topic_progress": topic_progress,
            "recent_activity": recent_activity
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_data():
    """Get dashboard summary data"""
    try:
        user_id = get_jwt_identity()
        
        # Get counts
        total_flashcards = Flashcard.query.filter_by(user_id=user_id).count()
        total_conversations = Conversation.query.filter_by(user_id=user_id).count()
        total_quizzes = Quiz.query.filter_by(user_id=user_id).count()
        
        # Get recent items
        recent_flashcards = Flashcard.query.filter_by(user_id=user_id)\
            .order_by(Flashcard.created_at.desc()).limit(5).all()
        
        recent_conversations = Conversation.query.filter_by(user_id=user_id)\
            .order_by(Conversation.updated_at.desc()).limit(5).all()
        
        # Get study streak
        today_sessions = StudySession.query.filter_by(user_id=user_id)\
            .filter(StudySession.started_at >= datetime.now().date()).count()
        
        # Most studied topics
        from sqlalchemy import func
        top_topics = db.session.query(
            UserProgress.topic,
            func.sum(UserProgress.total_study_time).label('total_time')
        ).filter_by(user_id=user_id)\
         .group_by(UserProgress.topic)\
         .order_by(func.sum(UserProgress.total_study_time).desc())\
         .limit(5).all()
        
        return jsonify({
            "summary": {
                "total_flashcards": total_flashcards,
                "total_conversations": total_conversations,
                "total_quizzes": total_quizzes,
                "studied_today": today_sessions > 0
            },
            "recent_flashcards": [
                {
                    "id": fc.id,
                    "question": fc.question[:100] + "..." if len(fc.question) > 100 else fc.question,
                    "topic": fc.topic,
                    "created_at": fc.created_at.isoformat()
                } for fc in recent_flashcards
            ],
            "recent_conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "updated_at": conv.updated_at.isoformat()
                } for conv in recent_conversations
            ],
            "top_topics": [
                {
                    "topic": topic,
                    "study_time": int(total_time)
                } for topic, total_time in top_topics
            ]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Search and History Routes
@app.route('/api/search', methods=['GET'])
@jwt_required()
def search_content():
    """Search user's content"""
    try:
        user_id = get_jwt_identity()
        query = request.args.get('q', '').strip()
        content_type = request.args.get('type', 'all')  # flashcards, conversations, quizzes, all
        
        if not query:
            return jsonify({"error": "Search query required"}), 400
        
        results = {}
        
        if content_type in ['all', 'flashcards']:
            flashcards = Flashcard.query.filter_by(user_id=user_id)\
                .filter(
                    (Flashcard.question.ilike(f'%{query}%')) |
                    (Flashcard.answer.ilike(f'%{query}%')) |
                    (Flashcard.topic.ilike(f'%{query}%'))
                ).limit(20).all()
            
            results['flashcards'] = [
                {
                    "id": fc.id,
                    "question": fc.question,
                    "answer": fc.answer,
                    "topic": fc.topic,
                    "created_at": fc.created_at.isoformat()
                } for fc in flashcards
            ]
        
        if content_type in ['all', 'conversations']:
            # Search in messages
            conversations = db.session.query(Conversation)\
                .join(Message)\
                .filter(Conversation.user_id == user_id)\
                .filter(Message.content.ilike(f'%{query}%'))\
                .distinct().limit(10).all()
            
            results['conversations'] = [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "updated_at": conv.updated_at.isoformat()
                } for conv in conversations
            ]
        
        if content_type in ['all', 'quizzes']:
            quizzes = Quiz.query.filter_by(user_id=user_id)\
                .filter(
                    (Quiz.title.ilike(f'%{query}%')) |
                    (Quiz.topic.ilike(f'%{query}%'))
                ).limit(10).all()
            
            results['quizzes'] = [
                {
                    "id": quiz.id,
                    "title": quiz.title,
                    "topic": quiz.topic,
                    "total_questions": quiz.total_questions,
                    "created_at": quiz.created_at.isoformat()
                } for quiz in quizzes
            ]
        
        return jsonify({
            "query": query,
            "results": results,
            "total_results": sum(len(v) for v in results.values())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
@jwt_required()
def get_user_history():
    """Get user's comprehensive history"""
    try:
        user_id = get_jwt_identity()
        days = int(request.args.get('days', 30))
        
        start_date = datetime.now() - timedelta(days=days)
        
        # Get recent activities
        recent_flashcards = Flashcard.query.filter_by(user_id=user_id)\
            .filter(Flashcard.created_at >= start_date)\
            .order_by(Flashcard.created_at.desc()).limit(20).all()
        
        recent_conversations = Conversation.query.filter_by(user_id=user_id)\
            .filter(Conversation.created_at >= start_date)\
            .order_by(Conversation.created_at.desc()).limit(20).all()
        
        recent_quizzes = Quiz.query.filter_by(user_id=user_id)\
            .filter(Quiz.created_at >= start_date)\
            .order_by(Quiz.created_at.desc()).limit(20).all()
        
        # Combine and sort by date
        history_items = []
        
        for fc in recent_flashcards:
            history_items.append({
                "type": "flashcard",
                "id": fc.id,
                "title": fc.question[:50] + "..." if len(fc.question) > 50 else fc.question,
                "topic": fc.topic,
                "created_at": fc.created_at.isoformat(),
                "metadata": {
                    "times_reviewed": fc.times_reviewed,
                    "mastery_level": fc.mastery_level
                }
            })
        
        for conv in recent_conversations:
            history_items.append({
                "type": "conversation",
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "metadata": {
                    "message_count": len(conv.messages),
                    "last_updated": conv.updated_at.isoformat()
                }
            })
        
        for quiz in recent_quizzes:
            history_items.append({
                "type": "quiz",
                "id": quiz.id,
                "title": quiz.title,
                "topic": quiz.topic,
                "created_at": quiz.created_at.isoformat(),
                "metadata": {
                    "total_questions": quiz.total_questions,
                    "difficulty": quiz.difficulty
                }
            })
        
        # Sort by creation date
        history_items.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            "history": history_items[:50],  # Limit to 50 most recent
            "period_days": days,
            "total_items": len(history_items)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Utility Routes
@app.route('/api/topics', methods=['GET'])
@jwt_required()
def get_user_topics():
    """Get user's studied topics"""
    try:
        user_id = get_jwt_identity()
        
        # Get topics from flashcards
        flashcard_topics = db.session.query(Flashcard.topic)\
            .filter_by(user_id=user_id)\
            .filter(Flashcard.topic.isnot(None))\
            .distinct().all()
        
        # Get topics from progress
        progress_topics = db.session.query(UserProgress.topic)\
            .filter_by(user_id=user_id)\
            .distinct().all()
        
        # Combine and deduplicate
        all_topics = set()
        for topic, in flashcard_topics:
            if topic and topic.strip():
                all_topics.add(topic.strip())
        
        for topic, in progress_topics:
            if topic and topic.strip():
                all_topics.add(topic.strip())
        
        topics_with_stats = []
        for topic in all_topics:
            # Get stats for each topic
            fc_count = Flashcard.query.filter_by(user_id=user_id, topic=topic).count()
            progress = UserProgress.query.filter_by(user_id=user_id, topic=topic).first()
            
            topics_with_stats.append({
                "topic": topic,
                "flashcard_count": fc_count,
                "mastery_level": progress.mastery_level if progress else 0.0,
                "last_studied": progress.last_studied.isoformat() if progress and progress.last_studied else None,
                "study_time": progress.total_study_time if progress else 0
            })
        
        # Sort by study time
        topics_with_stats.sort(key=lambda x: x['study_time'], reverse=True)
        
        return jsonify({
            "topics": topics_with_stats,
            "total_topics": len(topics_with_stats)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({"error": "File too large. Maximum size is 16MB"}), 413

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("BrainyPal Backend starting...")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print("Available endpoints:")
        print("- POST /api/auth/signup - User registration")
        print("- POST /api/auth/login - User login")
        print("- GET /api/chat/conversations - Get conversations")
        print("- POST /api/chat/send - Send chat message")
        print("- POST /api/upload - Upload files")
        print("- GET /api/flashcards - Get flashcards")
        print("- POST /api/flashcards/generate - Generate flashcards")
        print("- POST /api/quiz/generate - Generate quiz")
        print("- POST /api/practice - Generate practice questions")
        print("- GET /api/progress - Get user progress")
        print("- GET /api/search - Search content")
        print("- GET /api/history - Get user history")
    
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )