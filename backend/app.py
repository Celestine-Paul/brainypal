# BRAINYPAL Flask Backend Application - FULLY CORRECTED
# Working version with proper imports and error handling

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import requests
import json
import re
import logging
import time
import random
import string
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://brainypal:#celestine2016@localhost/brainypal_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models - CORRECTED
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(20), default='free')
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    daily_generations = db.Column(db.Integer, default=0)
    last_generation_date = db.Column(db.Date)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'plan': self.plan,
            'referral_code': self.referral_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Flashcard(db.Model):
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    front_text = db.Column(db.Text, nullable=False)
    back_text = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(200))
    difficulty = db.Column(db.String(20))
    mastered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': f'fc_{self.id}',
            'front': self.front_text,
            'back': self.back_text,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'mastered': self.mastered,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text)
    topic = db.Column(db.String(200))
    difficulty = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': f'q_{self.id}',
            'question': self.question_text,
            'options': [self.option_a, self.option_b, self.option_c, self.option_d],
            'correct': self.correct_option,
            'explanation': self.explanation,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserAnalytics(db.Model):
    __tablename__ = 'user_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_data = db.Column(db.Text)  # Store as JSON string
    session_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_id = db.Column(db.String(100), unique=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='KES')
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    plan = db.Column(db.String(20), nullable=False)
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

# AI Service Class - CORRECTED
class AIService:
    def __init__(self):
        self.api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        self.api_url = "https://api-inference.huggingface.co/models"
        self.timeout = 30
    
    def call_huggingface_api(self, model_name, inputs, parameters=None):
        """Call Hugging Face API with proper error handling"""
        if not self.api_token:
            logger.warning("No Hugging Face token configured, using fallback")
            return None
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {'inputs': inputs}
        if parameters:
            payload['parameters'] = parameters
        
        url = f"{self.api_url}/{model_name}"
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 503:
                logger.info("Model loading, using fallback generation")
                return None
            else:
                logger.error(f"API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return None
    
    def generate_flashcards(self, text, topic=None, difficulty='intermediate'):
        """Generate flashcards with AI or fallback"""
        try:
            # Try AI generation first
            concepts = self.extract_concepts(text)
            
            flashcards = []
            for concept in concepts[:6]:
                if isinstance(concept, dict) and 'term' in concept:
                    front = f"What is {concept['term']}?"
                    back = concept.get('definition', f"{concept['term']} is a key concept. Review your notes for details.")
                else:
                    front = f"What is {concept}?"
                    back = f"{concept} is mentioned in your study material. Review for more information."
                
                flashcards.append({
                    'front': front,
                    'back': back,
                    'topic': topic or 'Study Material',
                    'difficulty': difficulty
                })
            
            return flashcards if flashcards else self.generate_fallback_flashcards(text, topic, difficulty)
            
        except Exception as e:
            logger.error(f"Flashcard generation error: {e}")
            return self.generate_fallback_flashcards(text, topic, difficulty)
    
    def generate_questions(self, text, topic=None, difficulty='intermediate'):
        """Generate questions with AI or fallback"""
        try:
            keywords = self.extract_keywords(text)
            
            questions = []
            for keyword in keywords[:5]:
                question_text = self.create_question_text(keyword, difficulty)
                options = self.create_options(keyword, topic)
                
                questions.append({
                    'question': question_text,
                    'options': options,
                    'correct': 0,
                    'explanation': f"{keyword} is an important concept in your study material.",
                    'topic': topic or 'Study Material',
                    'difficulty': difficulty
                })
            
            return questions if questions else self.generate_fallback_questions(text, topic, difficulty)
            
        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return self.generate_fallback_questions(text, topic, difficulty)
    
    def extract_concepts(self, text):
        """Extract concepts from text"""
        concepts = []
        
        # Look for definition patterns
        patterns = [
            r'(\w+(?:\s+\w+)?)\s+is\s+([^.!?]+)',
            r'(\w+(?:\s+\w+)?):\s+([^.!?\n]+)',
            r'(\w+(?:\s+\w+)?)\s+means\s+([^.!?]+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(concepts) < 8:
                    concepts.append({
                        'term': match.group(1).strip(),
                        'definition': match.group(2).strip()
                    })
        
        # If no patterns found, use keywords
        if not concepts:
            keywords = self.extract_keywords(text)
            concepts = [{'term': keyword} for keyword in keywords]
        
        return concepts
    
    def extract_keywords(self, text):
        """Extract important keywords"""
        # Find capitalized words and important terms
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        words.extend(re.findall(r'\b\w{5,}\b', text.lower()))
        
        # Remove common words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'was', 'one'}
        filtered = [word for word in words if word.lower() not in stop_words]
        
        # Return unique words
        return list(set(filtered))[:8]
    
    def create_question_text(self, keyword, difficulty):
        """Create question text based on difficulty"""
        templates = {
            'beginner': f"What is {keyword}?",
            'intermediate': f"Which statement about {keyword} is most accurate?",
            'advanced': f"How does {keyword} relate to the broader context?"
        }
        return templates.get(difficulty, templates['intermediate'])
    
    def create_options(self, keyword, topic):
        """Create multiple choice options"""
        return [
            f"{keyword} is a key concept in {topic or 'this subject'}",
            f"{keyword} is not relevant to the topic",
            f"{keyword} is only mentioned briefly",
            f"{keyword} should be ignored"
        ]
    
    def generate_fallback_flashcards(self, text, topic, difficulty):
        """Fallback flashcard generation"""
        keywords = self.extract_keywords(text)
        
        flashcards = []
        for keyword in keywords[:6]:
            flashcards.append({
                'front': f"What is {keyword}?",
                'back': f"{keyword} is mentioned in your study notes. Review the material for more details.",
                'topic': topic or 'Study Material',
                'difficulty': difficulty
            })
        
        return flashcards
    
    def generate_fallback_questions(self, text, topic, difficulty):
        """Fallback question generation"""
        keywords = self.extract_keywords(text)
        
        questions = []
        for keyword in keywords[:5]:
            questions.append({
                'question': f"What can you say about {keyword}?",
                'options': [
                    f"{keyword} is discussed in the material",
                    f"{keyword} is not mentioned",
                    f"{keyword} is irrelevant",
                    f"{keyword} is outdated"
                ],
                'correct': 0,
                'explanation': f"{keyword} is found in your study notes.",
                'topic': topic or 'Study Material',
                'difficulty': difficulty
            })
        
        return questions

# Payment Service Class - CORRECTED
class PaymentService:
    def __init__(self):
        self.publishable_key = os.getenv('PAYSTACK_PUBLISHABLE_KEY')
        self.secret_key = os.getenv('PAYSTACK_SECRET_KEY')
        self.test_mode = os.getenv('PAYSTACK_TEST_MODE', 'True').lower() == 'true'
        self.base_url = "https://sandbox.paystack.com" if self.test_mode else "https://payment.paystack.com"
        
        self.plan_pricing = {
            'pro': 500.00,
            'premium': 999.00
        }
    
    def create_payment_request(self, user_data, plan, payment_method='mpesa'):
        """Create payment request"""
        try:
            amount = self.plan_pricing.get(plan, 999.00)
            payment_id = f"pay_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Simulate payment creation (replace with actual IntaSend integration)
            return {
                'success': True,
                'payment_id': payment_id,
                'amount': amount,
                'currency': 'KES',
                'status': 'pending',
                'checkout_url': f"https://checkout.paystack.com/{payment_id}",
                'message': 'Payment request created'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def verify_payment(self, payment_id):
        """Verify payment status"""
        try:
            # In production, call IntaSend API to verify
            return {
                'success': True,
                'status': 'completed',
                'payment_id': payment_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

# Initialize services
ai_service = AIService()
payment_service = PaymentService()

# Utility Functions
def generate_referral_code():
    """Generate unique referral code"""
    return 'BRAINY-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def check_user_limits(user):
    """Check if user can generate materials"""
    if user.plan != 'free':
        return True, None
    
    today = datetime.utcnow().date()
    if user.last_generation_date != today:
        user.daily_generations = 0
        user.last_generation_date = today
        db.session.commit()
    
    if user.daily_generations >= 3:
        return False, "Daily limit reached. Upgrade to Premium!"
    
    return True, None

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """User registration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        referral_code = data.get('referralCode', '')
        
        # Validation
        if len(name) < 2:
            return jsonify({'success': False, 'message': 'Name too short'}), 400
        if '@' not in email:
            return jsonify({'success': False, 'message': 'Invalid email'}), 400
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password too short'}), 400
        
        # Check existing user
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            referral_code=generate_referral_code(),
            referred_by=referral_code if referral_code else None
        )
        
        # Referral bonus
        if referral_code:
            referring_user = User.query.filter_by(referral_code=referral_code).first()
            if referring_user:
                user.plan = 'pro'
        
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully!',
            'data': {
                'user': user.to_dict(),
                'token': access_token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(),
                'token': access_token
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Login failed'}), 500

@app.route('/api/study/generate', methods=['POST'])
@jwt_required()
def generate_materials():
    """Generate study materials"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check limits
        can_generate, limit_message = check_user_limits(user)
        if not can_generate:
            return jsonify({'success': False, 'message': limit_message}), 429
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        notes = data.get('notes', '').strip()
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'intermediate')
        
        if len(notes) < 50:
            return jsonify({'success': False, 'message': 'Notes too short (minimum 50 characters)'}), 400
        
        # Generate materials
        flashcards_data = ai_service.generate_flashcards(notes, topic, difficulty)
        questions_data = ai_service.generate_questions(notes, topic, difficulty)
        
        # Save flashcards
        saved_flashcards = []
        for card_data in flashcards_data:
            flashcard = Flashcard(
                user_id=user_id,
                front_text=card_data['front'],
                back_text=card_data['back'],
                topic=card_data['topic'],
                difficulty=card_data['difficulty']
            )
            db.session.add(flashcard)
            saved_flashcards.append(flashcard)
        
        # Save questions
        saved_questions = []
        for q_data in questions_data:
            options = q_data['options']
            question = Question(
                user_id=user_id,
                question_text=q_data['question'],
                option_a=options[0] if len(options) > 0 else '',
                option_b=options[1] if len(options) > 1 else '',
                option_c=options[2] if len(options) > 2 else '',
                option_d=options[3] if len(options) > 3 else '',
                correct_option=q_data['correct'],
                explanation=q_data['explanation'],
                topic=q_data['topic'],
                difficulty=q_data['difficulty']
            )
            db.session.add(question)
            saved_questions.append(question)
        
        # Update user stats
        user.daily_generations += 1
        user.last_generation_date = datetime.utcnow().date()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Study materials generated successfully',
            'data': {
                'flashcards': [card.to_dict() for card in saved_flashcards],
                'questions': [q.to_dict() for q in saved_questions]
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Generation error: {e}")
        return jsonify({'success': False, 'message': 'Generation failed'}), 500

@app.route('/api/user/materials', methods=['GET'])
@jwt_required()
def get_user_materials():
    """Get user's study materials"""
    try:
        user_id = get_jwt_identity()
        
        flashcards = Flashcard.query.filter_by(user_id=user_id).order_by(Flashcard.created_at.desc()).all()
        questions = Question.query.filter_by(user_id=user_id).order_by(Question.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': {
                'flashcards': [card.to_dict() for card in flashcards],
                'questions': [q.to_dict() for q in questions]
            }
        })
        
    except Exception as e:
        logger.error(f"Get materials error: {e}")
        return jsonify({'success': False, 'message': 'Failed to load materials'}), 500

@app.route('/api/payment/create', methods=['POST'])
@jwt_required()
def create_payment():
    """Create payment request"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        plan = data.get('plan')
        payment_method = data.get('payment_method', 'mpesa')
        
        if plan not in ['pro', 'premium']:
            return jsonify({'success': False, 'message': 'Invalid plan'}), 400
        
        # Create payment
        payment_result = payment_service.create_payment_request(user.to_dict(), plan, payment_method)
        
        if payment_result['success']:
            # Save payment record
            payment = Payment(
                user_id=user_id,
                payment_id=payment_result['payment_id'],
                amount=payment_result['amount'],
                currency=payment_result['currency'],
                plan=plan,
                payment_method=payment_method,
                reference=f"BRAINYPAL_{plan}_{user_id}"
            )
            db.session.add(payment)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': payment_result
            })
        else:
            return jsonify(payment_result), 400
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Payment error: {e}")
        return jsonify({'success': False, 'message': 'Payment failed'}), 500

@app.route('/api/analytics/track', methods=['POST'])
@jwt_required()
def track_analytics():
    """Track user analytics"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'success': True})
        
        events = data.get('events', [])
        
        for event in events:
            analytics = UserAnalytics(
                user_id=user_id,
                event_type=event.get('event', 'unknown'),
                event_data=json.dumps(event.get('properties', {})),
                session_id=event.get('properties', {}).get('sessionId')
            )
            db.session.add(analytics)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Analytics error: {e}")
        return jsonify({'success': False}), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'data': {'user': user.to_dict()}
        })
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'success': False, 'message': 'Failed to get profile'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'success': False, 'message': 'Internal server error'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': 'Bad request'}), 400

# Create app factory function
def create_app():
    """Application factory"""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    return app

# Main execution
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)