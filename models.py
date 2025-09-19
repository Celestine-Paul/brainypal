from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    flashcards = db.relationship('Flashcard', backref='user', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade='all, delete-orphan')
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), default='New Conversation')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_user = db.Column(db.Boolean, nullable=False)  # True for user, False for AI
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional metadata
    ai_model = db.Column(db.String(100))  # Which AI model was used
    confidence = db.Column(db.Float)  # AI confidence score
    processing_time = db.Column(db.Float)  # Response time

class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(255))
    difficulty = db.Column(db.String(50), default='intermediate')
    
    # Source information
    source_type = db.Column(db.String(50))  # 'uploaded_file', 'topic_generation', 'manual'
    source_content = db.Column(db.Text)  # Original content it was generated from
    
    # Learning metrics
    times_reviewed = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime)
    mastery_level = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    
    # Generation metadata
    ai_confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(255))
    difficulty = db.Column(db.String(50), default='mixed')
    
    # Quiz metadata
    total_questions = db.Column(db.Integer, default=0)
    time_limit = db.Column(db.Integer)  # in minutes
    passing_score = db.Column(db.Float, default=70.0)
    
    # Source information
    source_type = db.Column(db.String(50))
    source_content = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, true_false, short_answer, fill_blank
    
    # Question data (stored as JSON)
    options = db.Column(db.Text)  # JSON array for multiple choice options
    correct_answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    
    # Metadata
    difficulty = db.Column(db.String(50), default='intermediate')
    points = db.Column(db.Integer, default=1)
    ai_confidence = db.Column(db.Float)
    
    def get_options(self):
        """Get options as Python list"""
        return json.loads(self.options) if self.options else []
    
    def set_options(self, options_list):
        """Set options from Python list"""
        self.options = json.dumps(options_list)

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Attempt data
    answers = db.Column(db.Text)  # JSON of question_id: answer pairs
    score = db.Column(db.Float)
    percentage = db.Column(db.Float)
    time_taken = db.Column(db.Integer)  # in seconds
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def get_answers(self):
        """Get answers as Python dict"""
        return json.loads(self.answers) if self.answers else {}
    
    def set_answers(self, answers_dict):
        """Set answers from Python dict"""
        self.answers = json.dumps(answers_dict)

class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_type = db.Column(db.String(50), nullable=False)  # 'flashcards', 'quiz', 'chat', 'practice'
    topic = db.Column(db.String(255))
    
    # Session data
    items_studied = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)  # in seconds
    
    # Performance metrics
    accuracy = db.Column(db.Float)  # percentage
    difficulty_level = db.Column(db.String(50))
    
    # Session metadata
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
class UploadedFile(db.Model):
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    
    # Content
    content = db.Column(db.Text)  # Extracted text content
    content_summary = db.Column(db.Text)
    
    # Processing status
    processed = db.Column(db.Boolean, default=False)
    processing_error = db.Column(db.Text)
    
    # Generated content counts
    flashcards_generated = db.Column(db.Integer, default=0)
    quiz_questions_generated = db.Column(db.Integer, default=0)
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    
    # Progress metrics
    total_study_time = db.Column(db.Integer, default=0)  # in seconds
    flashcards_reviewed = db.Column(db.Integer, default=0)
    quizzes_completed = db.Column(db.Integer, default=0)
    average_score = db.Column(db.Float, default=0.0)
    
    # Mastery tracking
    mastery_level = db.Column(db.Float, default=0.0)  # 0.0 to 1.0
    streak_days = db.Column(db.Integer, default=0)
    last_studied = db.Column(db.DateTime)
    
    # Timestamps
    first_studied = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'topic'),)

# Helper functions for database operations
def create_conversation(user_id, title="New Conversation"):
    """Create a new conversation"""
    conversation = Conversation(
        user_id=user_id,
        title=title
    )
    db.session.add(conversation)
    db.session.commit()
    return conversation

def add_message(conversation_id, content, is_user, **kwargs):
    """Add a message to a conversation"""
    message = Message(
        conversation_id=conversation_id,
        content=content,
        is_user=is_user,
        **kwargs
    )
    db.session.add(message)
    db.session.commit()
    return message

def save_flashcards(user_id, flashcards, source_type="ai_generated", source_content=""):
    """Save generated flashcards to database"""
    saved_flashcards = []
    
    for flashcard_data in flashcards:
        if isinstance(flashcard_data, dict) and 'question' in flashcard_data:
            flashcard = Flashcard(
                user_id=user_id,
                question=flashcard_data['question'],
                answer=flashcard_data['answer'],
                topic=flashcard_data.get('topic', ''),
                difficulty=flashcard_data.get('difficulty', 'intermediate'),
                source_type=source_type,
                source_content=source_content[:1000],  # Limit length
                ai_confidence=flashcard_data.get('confidence', 0.7)
            )
            db.session.add(flashcard)
            saved_flashcards.append(flashcard)
    
    db.session.commit()
    return saved_flashcards

def save_quiz(user_id, quiz_data, questions):
    """Save generated quiz to database"""
    quiz = Quiz(
        user_id=user_id,
        title=quiz_data.get('title', f"Quiz - {datetime.now().strftime('%Y-%m-%d')}"),
        topic=quiz_data.get('topic', ''),
        difficulty=quiz_data.get('difficulty', 'mixed'),
        total_questions=len(questions),
        source_type=quiz_data.get('source_type', 'ai_generated'),
        source_content=quiz_data.get('source_content', '')[:1000]
    )
    db.session.add(quiz)
    db.session.flush()  # Get the quiz ID
    
    # Save questions
    for q_data in questions:
        if isinstance(q_data, dict) and 'question' in q_data:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question=q_data['question'],
                question_type=q_data.get('type', 'short_answer'),
                correct_answer=str(q_data.get('answer', q_data.get('correct_answer', ''))),
                explanation=q_data.get('explanation', ''),
                difficulty=q_data.get('difficulty', 'intermediate'),
                ai_confidence=q_data.get('confidence', 0.7)
            )
            
            # Handle multiple choice options
            if q_data.get('options'):
                question.set_options(q_data['options'])
            
            db.session.add(question)
    
    db.session.commit()
    return quiz

def get_user_conversations(user_id, limit=20):
    """Get user's conversation history"""
    return Conversation.query.filter_by(user_id=user_id)\
        .order_by(Conversation.updated_at.desc())\
        .limit(limit).all()

def get_conversation_messages(conversation_id):
    """Get all messages in a conversation"""
    return Message.query.filter_by(conversation_id=conversation_id)\
        .order_by(Message.timestamp.asc()).all()

def get_user_flashcards(user_id, topic=None, limit=50):
    """Get user's flashcards, optionally filtered by topic"""
    query = Flashcard.query.filter_by(user_id=user_id)
    
    if topic:
        query = query.filter(Flashcard.topic.ilike(f'%{topic}%'))
    
    return query.order_by(Flashcard.created_at.desc()).limit(limit).all()

def get_user_quizzes(user_id, topic=None):
    """Get user's quizzes"""
    query = Quiz.query.filter_by(user_id=user_id)
    
    if topic:
        query = query.filter(Quiz.topic.ilike(f'%{topic}%'))
    
    return query.order_by(Quiz.created_at.desc()).all()

def update_flashcard_performance(flashcard_id, correct):
    """Update flashcard performance metrics"""
    flashcard = Flashcard.query.get(flashcard_id)
    if flashcard:
        flashcard.times_reviewed += 1
        if correct:
            flashcard.times_correct += 1
        
        # Calculate mastery level
        if flashcard.times_reviewed > 0:
            accuracy = flashcard.times_correct / flashcard.times_reviewed
            flashcard.mastery_level = min(1.0, accuracy * (flashcard.times_reviewed / 10))
        
        flashcard.last_reviewed = datetime.utcnow()
        db.session.commit()
    
    return flashcard

def save_study_session(user_id, session_data):
    """Save study session data"""
    session = StudySession(
        user_id=user_id,
        session_type=session_data.get('type', 'general'),
        topic=session_data.get('topic', ''),
        items_studied=session_data.get('items_studied', 0),
        correct_answers=session_data.get('correct_answers', 0),
        time_spent=session_data.get('time_spent', 0),
        difficulty_level=session_data.get('difficulty', 'mixed'),
        ended_at=datetime.utcnow()
    )
    
    # Calculate accuracy
    if session.items_studied > 0:
        session.accuracy = (session.correct_answers / session.items_studied) * 100
    
    db.session.add(session)
    db.session.commit()
    return session

def update_user_progress(user_id, topic, study_data):
    """Update or create user progress for a topic"""
    progress = UserProgress.query.filter_by(user_id=user_id, topic=topic).first()
    
    if not progress:
        progress = UserProgress(
            user_id=user_id,
            topic=topic,
            first_studied=datetime.utcnow()
        )
        db.session.add(progress)
    
    # Update metrics
    progress.total_study_time += study_data.get('time_spent', 0)
    progress.flashcards_reviewed += study_data.get('flashcards_reviewed', 0)
    progress.quizzes_completed += study_data.get('quizzes_completed', 0)
    
    # Update average score
    if study_data.get('score'):
        if progress.average_score == 0:
            progress.average_score = study_data['score']
        else:
            # Running average
            progress.average_score = (progress.average_score + study_data['score']) / 2
    
    # Update streak
    if progress.last_studied:
        days_since = (datetime.utcnow() - progress.last_studied).days
        if days_since == 1:
            progress.streak_days += 1
        elif days_since > 1:
            progress.streak_days = 1
    else:
        progress.streak_days = 1
    
    progress.last_studied = datetime.utcnow()
    db.session.commit()
    
    return progress