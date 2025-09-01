# BrainyPal Database Models
# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    subscription = db.Column(db.String(20), default='free')  # free, premium, pro
    subscription_start = db.Column(db.DateTime, nullable=True)
    subscription_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional payment metadata
    metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    refund_amount = db.Column(db.Float, default=0.0)
    refund_reason = db.Column(db.String(255), nullable=True)
    intasend_payment_id = db.Column(db.String(100), unique=True, nullable=True)
    
    def get_metadata(self):
        """Get metadata as dictionary"""
        try:
            return json.loads(self.metadata) if self.metadata else {}
        except:
            return {}
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'plan': self.plan,
            'status': self.status,
            'createdAt': self.created_at.isoformat(),
            'metadata': self.get_metadata()
        }

class Activity(db.Model):
    """User activity tracking model"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    activity_type = db.Column(db.String(50), nullable=False, index=True)  # study, quiz, generate, login, etc.
    description = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)  # JSON string for additional details
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Related object IDs (optional)
    flashcard_id = db.Column(db.Integer, db.ForeignKey('flashcards.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=True)
    
    def get_details(self):
        """Get details as dictionary"""
        try:
            return json.loads(self.details) if self.details else {}
        except:
            return {}
    
    def to_dict(self):
        """Convert activity to dictionary"""
        return {
            'id': self.id,
            'type': self.activity_type,
            'description': self.description,
            'details': self.get_details(),
            'createdAt': self.created_at.isoformat(),
            'flashcardId': self.flashcard_id,
            'quizId': self.quiz_id
        }

class StudySession(db.Model):
    """Study session tracking model"""
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)  # Calculated duration
    cards_reviewed = db.Column(db.Integer, default=0)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    
    # Session metadata
    topics_studied = db.Column(db.Text, nullable=True)  # JSON array of topics
    difficulty_focus = db.Column(db.String(20), nullable=True)
    session_type = db.Column(db.String(20), default='mixed')  # flashcards, quiz, mixed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_duration(self):
        """Calculate session duration"""
        if self.end_time and self.start_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
    
    def get_topics_studied(self):
        """Get topics studied as list"""
        try:
            return json.loads(self.topics_studied) if self.topics_studied else []
        except:
            return []
    
    @property
    def accuracy_rate(self):
        """Calculate session accuracy rate"""
        return (self.correct_answers / self.questions_answered * 100) if self.questions_answered > 0 else 0
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'startTime': self.start_time.isoformat(),
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'durationMinutes': self.duration_minutes,
            'cardsReviewed': self.cards_reviewed,
            'questionsAnswered': self.questions_answered,
            'correctAnswers': self.correct_answers,
            'accuracyRate': self.accuracy_rate,
            'topicsStudied': self.get_topics_studied(),
            'sessionType': self.session_type
        }

class APIUsage(db.Model):
    """API usage tracking for rate limiting"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    endpoint = db.Column(db.String(100), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    date = db.Column(db.Date, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def track_usage(user_id, endpoint):
        """Track API usage for rate limiting"""
        today = datetime.utcnow().date()
        usage = APIUsage.query.filter_by(
            user_id=user_id,
            endpoint=endpoint,
            date=today
        ).first()
        
        if usage:
            usage.request_count += 1
            usage.updated_at = datetime.utcnow()
        else:
            usage = APIUsage(
                user_id=user_id,
                endpoint=endpoint,
                request_count=1,
                date=today
            )
            db.session.add(usage)
        
        db.session.commit()
        return usage.request_count
    
    @staticmethod
    def get_daily_usage(user_id, endpoint):
        """Get daily usage count for an endpoint"""
        today = datetime.utcnow().date()
        usage = APIUsage.query.filter_by(
            user_id=user_id,
            endpoint=endpoint,
            date=today
        ).first()
        
        return usage.request_count if usage else 0

class Subscription(db.Model):
    """Subscription management model"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    plan = db.Column(db.String(20), nullable=False)  # free, premium, pro
    status = db.Column(db.String(20), default='active')  # active, cancelled, expired, suspended
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    
    # paystack integration
    paystack_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    paystack_customer_id = db.Column(db.String(100), nullable=True)
    
    # Billing
    amount = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    billing_cycle = db.Column(db.String(20), default='monthly')  # monthly, yearly
    
    # Metadata
    features = db.Column(db.Text, nullable=True)  # JSON string of enabled features
    auto_renew = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status != 'active':
            return False
        return not self.end_date or self.end_date > datetime.utcnow()
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if not self.end_date:
            return None
        delta = self.end_date - datetime.utcnow()
        return max(0, delta.days)
    
    def get_features(self):
        """Get enabled features as list"""
        try:
            return json.loads(self.features) if self.features else []
        except:
            return []
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'plan': self.plan,
            'status': self.status,
            'isActive': self.is_active,
            'startDate': self.start_date.isoformat(),
            'endDate': self.end_date.isoformat() if self.end_date else None,
            'daysRemaining': self.days_remaining,
            'amount': self.amount,
            'currency': self.currency,
            'billingCycle': self.billing_cycle,
            'features': self.get_features(),
            'autoRenew': self.auto_renew
        }

class Topic(db.Model):
    """Topic categorization model"""
    __tablename__ = 'topics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)  # science, math, history, etc.
    icon = db.Column(db.String(10), nullable=True)  # Emoji icon
    color = db.Column(db.String(7), nullable=True)  # Hex color code
    
    # Statistics
    total_flashcards = db.Column(db.Integer, default=0)
    total_users = db.Column(db.Integer, default=0)
    difficulty_distribution = db.Column(db.Text, nullable=True)  # JSON string
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def update_statistics(self):
        """Update topic statistics"""
        self.total_flashcards = Flashcard.query.filter_by(topic=self.name).count()
        self.total_users = db.session.query(Flashcard.user_id).filter_by(topic=self.name).distinct().count()
        
        # Calculate difficulty distribution
        difficulties = db.session.query(
            Flashcard.difficulty,
            db.func.count(Flashcard.id)
        ).filter_by(topic=self.name).group_by(Flashcard.difficulty).all()
        
        distribution = {diff: count for diff, count in difficulties}
        self.difficulty_distribution = json.dumps(distribution)
    
    def to_dict(self):
        """Convert topic to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'color': self.color,
            'totalFlashcards': self.total_flashcards,
            'totalUsers': self.total_users,
            'difficultyDistribution': json.loads(self.difficulty_distribution) if self.difficulty_distribution else {}
        }

class UserPreferences(db.Model):
    """User preferences model"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Study preferences
    preferred_difficulty = db.Column(db.String(20), default='intermediate')
    daily_goal = db.Column(db.Integer, default=10)  # Cards per day
    study_reminders = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.Time, nullable=True)
    
    # Interface preferences
    theme = db.Column(db.String(20), default='light')  # light, dark, auto
    animations_enabled = db.Column(db.Boolean, default=True)
    sound_effects = db.Column(db.Boolean, default=True)
    
    # Learning preferences
    spaced_repetition = db.Column(db.Boolean, default=True)
    show_difficulty_badges = db.Column(db.Boolean, default=True)
    auto_advance = db.Column(db.Boolean, default=False)
    
    # Privacy preferences
    public_profile = db.Column(db.Boolean, default=False)
    share_progress = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert preferences to dictionary"""
        return {
            'preferredDifficulty': self.preferred_difficulty,
            'dailyGoal': self.daily_goal,
            'studyReminders': self.study_reminders,
            'reminderTime': self.reminder_time.strftime('%H:%M') if self.reminder_time else None,
            'theme': self.theme,
            'animationsEnabled': self.animations_enabled,
            'soundEffects': self.sound_effects,
            'spacedRepetition': self.spaced_repetition,
            'showDifficultyBadges': self.show_difficulty_badges,
            'autoAdvance': self.auto_advance,
            'publicProfile': self.public_profile,
            'shareProgress': self.share_progress
        }

# Database utility functions
def init_database():
    
    """Initialize database with default data"""
    db.create_all()
    
    # Create default topics if they don't exist
    default_topics = [
        {'name': 'Mathematics', 'category': 'stem', 'icon': '🔢', 'color': '#4299e1'},
        {'name': 'Science', 'category': 'stem', 'icon': '🔬', 'color': '#48bb78'},
        {'name': 'History', 'category': 'humanities', 'icon': '📚', 'color': '#ed8936'},
        {'name': 'Literature', 'category': 'humanities', 'icon': '📖', 'color': '#9f7aea'},
        {'name': 'Language', 'category': 'language', 'icon': '🗣️', 'color': '#f56565'},
        {'name': 'Computer Science', 'category': 'stem', 'icon': '💻', 'color': '#38b2ac'},
        {'name': 'Biology', 'category': 'stem', 'icon': '🧬', 'color': '#68d391'},
        {'name': 'Physics', 'category': 'stem', 'icon': '⚛️', 'color': '#4fd1c7'},
        {'name': 'Chemistry', 'category': 'stem', 'icon': '🧪', 'color': '#fc8181'},
        {'name': 'Geography', 'category': 'social', 'icon': '🌍', 'color': '#4ecdc4'}
    ]
    
    for topic_data in default_topics:
        existing_topic = Topic.query.filter_by(name=topic_data['name']).first()
        if not existing_topic:
            topic = Topic(**topic_data)
            db.session.add(topic)
    
    db.session.commit()
    print("Database initialized with default topics")

# Database migration helpers
def upgrade_database():
    """Upgrade database schema"""
    try:
        # Add any schema migrations here
        db.session.commit()
        print("Database upgraded successfully")
    except Exception as e:
        print(f"Database upgrade failed: {e}")
        db.session.rollback()

def backup_database():
    """Create database backup"""
    import subprocess
    import os
    from flask import current_app
    
    try:
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{backup_dir}/brainypal_backup_{timestamp}.sql"
        
        # For SQLite
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if 'sqlite' in db_uri:
            import shutil
            db_file = db_uri.replace('sqlite:///', '')
            shutil.copy2(db_file, f"{backup_dir}/brainypal_{timestamp}.db")
        
        print(f"Database backup created: {backup_file}")
        return backup_file
        
    except Exception as e:
        print(f"Database backup failed: {e}")
        return None

# Model relationships and constraints
# Add foreign key constraints and indexes for better performance
def init_database():
    """Initialize database with default data"""
    db.create_all()
    
    # Create default topics if they don't exist
    default_topics = [
        {'name': 'Mathematics', 'category': 'stem', 'icon': '🔢', 'color': '#4299e1'},
        {'name': 'Science', 'category': 'stem', 'icon': '🔬', 'color': '#48bb78'},
        {'name': 'History', 'category': 'humanities', 'icon': '📚', 'color': '#ed8936'},
        {'name': 'Literature', 'category': 'humanities', 'icon': '📖', 'color': '#9f7aea'},
        {'name': 'Language', 'category': 'language', 'icon': '🗣️', 'color': '#f56565'},
        {'name': 'Computer Science', 'category': 'stem', 'icon': '💻', 'color': '#38b2ac'},
        {'name': 'Biology', 'category': 'stem', 'icon': '🧬', 'color': '#68d391'},
        {'name': 'Physics', 'category': 'stem', 'icon': '⚛️', 'color': '#4fd1c7'},
        {'name': 'Chemistry', 'category': 'stem', 'icon': '🧪', 'color': '#fc8181'},
        {'name': 'Geography', 'category': 'social', 'icon': '🌍', 'color': '#4ecdc4'}
    ]
    
    for topic_data in default_topics:
        existing_topic = Topic.query.filter_by(name=topic_data['name']).first()
        if not existing_topic:
            topic = Topic(**topic_data)
            db.session.add(topic)
    
    try:
        db.session.commit()
        print("Database initialized with default topics")
    except Exception as e:
        print(f"Database initialization error: {e}")
        db.session.rollback()

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        init_database()  # call your database init function
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    auth_method = db.Column(db.String(20), default='email')  # email, google, github
    profile_picture = db.Column(db.String(255), nullable=True)
    preferences = db.Column(db.Text, nullable=True)  # JSON string for user preferences
    
    # Relationships
    flashcards = db.relationship('Flashcard', backref='user', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade='all, delete-orphan')
    progress = db.relationship('Progress', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.preferences:
            self.preferences = json.dumps({
                'theme': 'light',
                'notifications': True,
                'difficulty_preference': 'intermediate',
                'daily_goal': 10
            })
    
    @property
    def is_premium(self):
        """Check if user has premium subscription"""
        return self.subscription in ['premium', 'pro']
    
    @property
    def subscription_active(self):
        """Check if subscription is currently active"""
        if self.subscription == 'free':
            return True
        return self.subscription_end and self.subscription_end > datetime.utcnow()
    
    def get_preferences(self):
        """Get user preferences as dictionary"""
        try:
            return json.loads(self.preferences) if self.preferences else {}
        except:
            return {}
    
    def update_preferences(self, new_preferences):
        """Update user preferences"""
        current = self.get_preferences()
        current.update(new_preferences)
        self.preferences = json.dumps(current)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'subscription': self.subscription,
            'subscriptionActive': self.subscription_active,
            'createdAt': self.created_at.isoformat(),
            'lastLogin': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.get_preferences()
        }

class Flashcard(db.Model):
    """Flashcard model for storing study cards"""
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default='intermediate')  # beginner, intermediate, advanced
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Spaced repetition fields
    review_count = db.Column(db.Integer, default=0)
    last_reviewed = db.Column(db.DateTime, nullable=True)
    next_review = db.Column(db.DateTime, nullable=True)
    interval = db.Column(db.Integer, default=1)  # Days until next review
    ease_factor = db.Column(db.Float, default=2.5)  # Spaced repetition ease factor
    
    # Metadata
    source = db.Column(db.String(50), default='ai_generated')  # ai_generated, manual, imported
    tags = db.Column(db.Text, nullable=True)  # JSON string for tags
    is_favorite = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False)
    
    def __init__(self, **kwargs):
        super(Flashcard, self).__init__(**kwargs)
        if not self.next_review:
            self.next_review = datetime.utcnow()
    
    @property
    def is_due(self):
        """Check if flashcard is due for review"""
        return not self.next_review or self.next_review <= datetime.utcnow()
    
    def get_tags(self):
        """Get tags as list"""
        try:
            return json.loads(self.tags) if self.tags else []
        except:
            return []
    
    def add_tag(self, tag):
        """Add a tag to the flashcard"""
        tags = self.get_tags()
        if tag not in tags:
            tags.append(tag)
            self.tags = json.dumps(tags)
    
    def remove_tag(self, tag):
        """Remove a tag from the flashcard"""
        tags = self.get_tags()
        if tag in tags:
            tags.remove(tag)
            self.tags = json.dumps(tags)
    
    def to_dict(self):
        """Convert flashcard to dictionary"""
        return {
            'id': self.id,
            'topic': self.topic,
            'question': self.question,
            'answer': self.answer,
            'difficulty': self.difficulty,
            'createdAt': self.created_at.isoformat(),
            'reviewCount': self.review_count,
            'lastReviewed': self.last_reviewed.isoformat() if self.last_reviewed else None,
            'nextReview': self.next_review.isoformat() if self.next_review else None,
            'tags': self.get_tags(),
            'isFavorite': self.is_favorite,
            'isDue': self.is_due
        }

class Quiz(db.Model):
    """Quiz question model"""
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    topic = db.Column(db.String(100), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON string of options array
    correct_answer = db.Column(db.Integer, nullable=False)  # Index of correct option
    explanation = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default='intermediate')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Performance tracking
    times_answered = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    
    # Metadata
    source = db.Column(db.String(50), default='ai_generated')
    tags = db.Column(db.Text, nullable=True)  # JSON string for tags
    
    @property
    def accuracy_rate(self):
        """Calculate accuracy rate for this question"""
        return (self.times_correct / self.times_answered * 100) if self.times_answered > 0 else 0
    
    def get_options(self):
        """Get options as list"""
        try:
            return json.loads(self.options) if self.options else []
        except:
            return []
    
    def set_options(self, options_list):
        """Set options from list"""
        self.options = json.dumps(options_list)
    
    def record_answer(self, is_correct):
        """Record an answer attempt"""
        self.times_answered += 1
        if is_correct:
            self.times_correct += 1
    
    def to_dict(self):
        """Convert quiz to dictionary"""
        return {
            'id': self.id,
            'topic': self.topic,
            'question': self.question,
            'options': self.get_options(),
            'correctAnswer': self.correct_answer,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'createdAt': self.created_at.isoformat(),
            'accuracyRate': self.accuracy_rate,
            'timesAnswered': self.times_answered
        }

class Progress(db.Model):
    """User progress tracking model"""
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    # Study statistics
    total_cards = db.Column(db.Integer, default=0)
    cards_studied = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    
    # Streak tracking
    streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_study_date = db.Column(db.Date, nullable=True)
    
    # Time tracking
    study_time = db.Column(db.Integer, default=0)  # Total study time in minutes
    sessions_completed = db.Column(db.Integer, default=0)
    
    # Achievement tracking
    achievements = db.Column(db.Text, nullable=True)  # JSON string of unlocked achievements
    level = db.Column(db.Integer, default=1)
    experience_points = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def accuracy_percentage(self):
        """Calculate overall accuracy percentage"""
        return (self.correct_answers / self.total_questions * 100) if self.total_questions > 0 else 0
    
    @property
    def completion_percentage(self):
        """Calculate study completion percentage"""
        return (self.cards_studied / self.total_cards * 100) if self.total_cards > 0 else 0
    
    def get_achievements(self):
        """Get achievements as list"""
        try:
            return json.loads(self.achievements) if self.achievements else []
        except:
            return []
    
    def add_achievement(self, achievement):
        """Add a new achievement"""
        achievements = self.get_achievements()
        if achievement not in achievements:
            achievements.append(achievement)
            self.achievements = json.dumps(achievements)
            return True
        return False
    
    def add_experience(self, points):
        """Add experience points and check for level up"""
        self.experience_points += points
        new_level = self.calculate_level(self.experience_points)
        
        if new_level > self.level:
            self.level = new_level
            return True  # Level up occurred
        return False
    
    @staticmethod
    def calculate_level(exp):
        """Calculate level based on experience points"""
        # Level formula: level = floor(sqrt(exp / 100)) + 1
        import math
        return math.floor(math.sqrt(exp / 100)) + 1
    
    def update_streak(self, studied_today=True):
        """Update study streak"""
        from datetime import timedelta
        today = datetime.utcnow().date()
        
        if studied_today:
            if self.last_study_date == today:
                # Already studied today, no change
                return False
            elif self.last_study_date == today - timedelta(days=1):
                # Studied yesterday, continue streak
                self.streak += 1
            else:
                # Streak broken, restart
                self.streak = 1
            
            self.last_study_date = today
            
            # Update longest streak
            if self.streak > self.longest_streak:
                self.longest_streak = self.streak
            
            return True
        
        return False
    
    def to_dict(self):
        """Convert progress to dictionary"""
        return {
            'totalCards': self.total_cards,
            'cardsStudied': self.cards_studied,
            'correctAnswers': self.correct_answers,
            'totalQuestions': self.total_questions,
            'streak': self.streak,
            'longestStreak': self.longest_streak,
            'studyTime': self.study_time,
            'sessionsCompleted': self.sessions_completed,
            'accuracyPercentage': self.accuracy_percentage,
            'completionPercentage': self.completion_percentage,
            'level': self.level,
            'experiencePoints': self.experience_points,
            'achievements': self.get_achievements(),
            'lastStudyDate': self.last_study_date.isoformat() if self.last_study_date else None
        }

class Payment(db.Model):
    """Payment tracking model"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)  # Amount in dollars
    currency = db.Column(db.String(3), default='USD')
    plan = db.Column(db.String(20), nullable=False)  # premium, pro
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    stripe_payment_id = db.Column(db.String(100), unique=True, nullable=True)
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    created_at = db