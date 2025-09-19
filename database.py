"""
BrainyPal Database Manager
=========================
Complete database setup and management for BrainyPal application.
NO PRE-FORMED QUESTIONS - EVERYTHING DYNAMIC
"""

import mysql.connector
from mysql.connector import Error, pooling
import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Complete database management for BrainyPal application
    Handles connections, user management, and all database operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize database manager with configuration
        
        Args:
            config: Dictionary with database configuration
                   {
                       'host': 'localhost',
                       'database': 'brainypal_db',
                       'user': 'brainypal_app',
                       'password': 'BrainyPal2024!SecureApp#',
                       'pool_name': 'brainypal_pool',
                       'pool_size': 10
                   }
        """
        self.config = config
        self.connection_pool = None
        self.setup_connection_pool()
    
    def setup_connection_pool(self):
        """Setup MySQL connection pool for better performance"""
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=self.config.get('pool_name', 'brainypal_pool'),
                pool_size=self.config.get('pool_size', 10),
                pool_reset_session=True,
                host=self.config['host'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False,
                time_zone='+00:00'
            )
            logger.info("Database connection pool created successfully")
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()

    def create_database_schema(self):
        """
        Create the complete BrainyPal database schema
        This is typically run once during initial setup
        """
        
        # SQL commands for creating the complete schema
        schema_commands = [
            # Create users table
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                plan ENUM('free', 'premium', 'pro') DEFAULT 'free',
                is_verified BOOLEAN DEFAULT FALSE,
                verification_code VARCHAR(6) DEFAULT NULL,
                verification_expires DATETIME DEFAULT NULL,
                login_attempts INT DEFAULT 0,
                locked_until TIMESTAMP NULL DEFAULT NULL,
                last_login TIMESTAMP NULL DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_email (email),
                INDEX idx_plan (plan),
                INDEX idx_created_at (created_at)
            )
            """,
            
            # Create user sessions table
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_token VARCHAR(255) NOT NULL,
                expires_at DATETIME NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_token (session_token),
                INDEX idx_expires (expires_at)
            )
            """,
            
            # Create conversations table
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) DEFAULT 'New Conversation',
                topic VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_updated_at (updated_at),
                INDEX idx_topic (topic)
            )
            """,
            
            # Create messages table
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT NOT NULL,
                content TEXT NOT NULL,
                is_user BOOLEAN NOT NULL,
                ai_model VARCHAR(100) DEFAULT 'huggingface',
                confidence FLOAT DEFAULT NULL,
                processing_time FLOAT DEFAULT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                INDEX idx_conversation_id (conversation_id),
                INDEX idx_timestamp (timestamp),
                INDEX idx_is_user (is_user),
                FULLTEXT(content)
            )
            """,
            
            # Create flashcards table - ALL DYNAMICALLY GENERATED
            """
            CREATE TABLE IF NOT EXISTS flashcards (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                topic VARCHAR(255) DEFAULT NULL,
                difficulty ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
                
                source_type ENUM('topic_generation', 'file_upload', 'conversation') NOT NULL,
                source_content TEXT DEFAULT NULL,
                generation_session VARCHAR(100) NOT NULL,
                
                times_reviewed INT DEFAULT 0,
                times_correct INT DEFAULT 0,
                last_reviewed DATETIME DEFAULT NULL,
                mastery_level FLOAT DEFAULT 0.0,
                
                ai_confidence FLOAT DEFAULT 0.7,
                generation_prompt TEXT DEFAULT NULL,
                variation_seed VARCHAR(50) DEFAULT NULL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_topic (topic),
                INDEX idx_source_type (source_type),
                INDEX idx_generation_session (generation_session),
                INDEX idx_created_at (created_at),
                FULLTEXT(question, answer)
            )
            """,
            
            # Create quizzes table
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                topic VARCHAR(255) DEFAULT NULL,
                difficulty ENUM('beginner', 'intermediate', 'advanced', 'mixed') DEFAULT 'mixed',
                
                total_questions INT DEFAULT 0,
                time_limit INT DEFAULT NULL,
                passing_score FLOAT DEFAULT 70.0,
                
                source_type ENUM('topic_generation', 'file_upload', 'conversation') NOT NULL,
                source_content TEXT DEFAULT NULL,
                generation_session VARCHAR(100) NOT NULL,
                variation_seed VARCHAR(50) DEFAULT NULL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_topic (topic),
                INDEX idx_generation_session (generation_session),
                INDEX idx_created_at (created_at)
            )
            """,
            
            # Create quiz questions table
            """
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                quiz_id INT NOT NULL,
                question TEXT NOT NULL,
                question_type ENUM('multiple_choice', 'true_false', 'short_answer', 'fill_blank', 'essay') NOT NULL,
                
                correct_answer TEXT NOT NULL,
                options JSON DEFAULT NULL,
                explanation TEXT DEFAULT NULL,
                
                difficulty ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
                points INT DEFAULT 1,
                ai_confidence FLOAT DEFAULT 0.7,
                generation_prompt TEXT DEFAULT NULL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
                INDEX idx_quiz_id (quiz_id),
                INDEX idx_question_type (question_type),
                INDEX idx_difficulty (difficulty),
                FULLTEXT(question, explanation)
            )
            """,
            
            # Create quiz attempts table
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                quiz_id INT NOT NULL,
                user_id INT NOT NULL,
                
                answers JSON NOT NULL,
                score FLOAT DEFAULT 0,
                percentage FLOAT DEFAULT 0,
                time_taken INT DEFAULT NULL,
                
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP DEFAULT NULL,
                
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_quiz_id (quiz_id),
                INDEX idx_user_id (user_id),
                INDEX idx_started_at (started_at)
            )
            """,
            
            # Create uploaded files table
            """
            CREATE TABLE IF NOT EXISTS uploaded_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_type VARCHAR(50) NOT NULL,
                file_size INT NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                
                content LONGTEXT DEFAULT NULL,
                content_summary TEXT DEFAULT NULL,
                
                processed BOOLEAN DEFAULT FALSE,
                processing_error TEXT DEFAULT NULL,
                
                flashcards_generated INT DEFAULT 0,
                quiz_questions_generated INT DEFAULT 0,
                
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP DEFAULT NULL,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_processed (processed),
                INDEX idx_uploaded_at (uploaded_at),
                FULLTEXT(content)
            )
            """,
            
            # Create study sessions table
            """
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_type ENUM('flashcards', 'quiz', 'chat', 'practice', 'file_upload') NOT NULL,
                topic VARCHAR(255) DEFAULT NULL,
                
                items_studied INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                time_spent INT DEFAULT 0,
                
                accuracy FLOAT DEFAULT NULL,
                difficulty_level ENUM('beginner', 'intermediate', 'advanced', 'mixed') DEFAULT 'mixed',
                
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP DEFAULT NULL,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_session_type (session_type),
                INDEX idx_topic (topic),
                INDEX idx_started_at (started_at)
            )
            """,
            
            # Create user progress table
            """
            CREATE TABLE IF NOT EXISTS user_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                topic VARCHAR(255) NOT NULL,
                
                total_study_time INT DEFAULT 0,
                flashcards_reviewed INT DEFAULT 0,
                quizzes_completed INT DEFAULT 0,
                average_score FLOAT DEFAULT 0.0,
                
                mastery_level FLOAT DEFAULT 0.0,
                streak_days INT DEFAULT 0,
                last_studied DATE DEFAULT NULL,
                
                first_studied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY unique_user_topic (user_id, topic),
                INDEX idx_user_id (user_id),
                INDEX idx_topic (topic),
                INDEX idx_mastery_level (mastery_level),
                INDEX idx_last_studied (last_studied)
            )
            """,
            
            # Create generation sessions table
            """
            CREATE TABLE IF NOT EXISTS generation_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id VARCHAR(100) NOT NULL UNIQUE,
                generation_type ENUM('flashcards', 'quiz', 'practice', 'chat') NOT NULL,
                
                topic VARCHAR(255) DEFAULT NULL,
                difficulty ENUM('beginner', 'intermediate', 'advanced', 'mixed') DEFAULT 'mixed',
                content_source TEXT DEFAULT NULL,
                variation_seed VARCHAR(50) NOT NULL,
                
                ai_model VARCHAR(100) DEFAULT 'huggingface',
                prompt_used TEXT DEFAULT NULL,
                items_generated INT DEFAULT 0,
                generation_time FLOAT DEFAULT NULL,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_session_id (session_id),
                INDEX idx_generation_type (generation_type),
                INDEX idx_topic (topic),
                INDEX idx_created_at (created_at)
            )
            """,
            
            # Create app settings table
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(100) NOT NULL UNIQUE,
                setting_value TEXT NOT NULL,
                description TEXT DEFAULT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                INDEX idx_setting_key (setting_key)
            )
            """,
            
            # Create audit logs table
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NULL,
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(50) NULL,
                resource_id INT NULL,
                ip_address VARCHAR(45) NULL,
                user_agent TEXT NULL,
                details JSON NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_action (action),
                INDEX idx_timestamp (timestamp)
            )
            """,
            
            # Create rate limits table
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ip_address VARCHAR(45) NOT NULL,
                endpoint VARCHAR(100) NOT NULL,
                request_count INT DEFAULT 1,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT FALSE,
                
                UNIQUE KEY unique_ip_endpoint (ip_address, endpoint),
                INDEX idx_ip_address (ip_address),
                INDEX idx_window_start (window_start)
            )
            """
        ]
        
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                for command in schema_commands:
                    cursor.execute(command)
                    logger.info(f"Executed: {command[:50]}...")
                
                connection.commit()
                logger.info("Database schema created successfully")
                
                # Insert default app settings
                self.insert_default_settings(connection)
                
        except Error as e:
            logger.error(f"Error creating database schema: {e}")
            raise

    def insert_default_settings(self, connection):
        """Insert default application settings"""
        default_settings = [
            ('ai_model_default', 'huggingface', 'Default AI model for content generation'),
            ('max_flashcards_per_generation', '10', 'Maximum flashcards generated per request'),
            ('max_quiz_questions_per_generation', '8', 'Maximum quiz questions per generation'),
            ('free_plan_daily_limit_chat', '10', 'Free plan daily chat message limit'),
            ('free_plan_daily_limit_flashcards', '3', 'Free plan daily flashcard generation limit'),
            ('free_plan_daily_limit_uploads', '1', 'Free plan daily file upload limit'),
            ('content_variation_enabled', 'true', 'Enable content variation on each generation'),
            ('premium_price_ksh', '500', 'Premium plan price in KSH'),
            ('pro_price_ksh', '1000', 'Pro plan price in KSH'),
            ('session_timeout_minutes', '60', 'User session timeout in minutes'),
            ('max_login_attempts', '5', 'Maximum login attempts before account lockout'),
            ('lockout_duration_minutes', '30', 'Account lockout duration in minutes'),
            ('password_min_length', '8', 'Minimum password length requirement'),
            ('require_email_verification', 'true', 'Require email verification for new accounts'),
            ('max_file_size_mb', '10', 'Maximum file upload size in MB'),
            ('allowed_file_types', 'pdf,txt,docx,md', 'Allowed file types for upload')
        ]
        
        cursor = connection.cursor()
        insert_query = """
        INSERT IGNORE INTO app_settings (setting_key, setting_value, description) 
        VALUES (%s, %s, %s)
        """
        
        cursor.executemany(insert_query, default_settings)
        logger.info("Default app settings inserted")

    # =============================================================================
    # USER MANAGEMENT METHODS
    # =============================================================================
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""
        try:
            salt, password_hash = stored_hash.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except:
            return False
    
    def generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return f"{secrets.randbelow(1000000):06d}"
    
    def increment_login_attempts(self, user_id: int, connection):
        """Increment login attempts and lock account if necessary"""
        cursor = connection.cursor()
        
        cursor.execute(
            "UPDATE users SET login_attempts = login_attempts + 1 WHERE id = %s",
            (user_id,)
        )
        
        # Check if we need to lock the account
        cursor.execute("SELECT login_attempts FROM users WHERE id = %s", (user_id,))
        attempts = cursor.fetchone()[0]
        
        max_attempts = int(self.get_setting('max_login_attempts', '5'))
        lockout_duration = int(self.get_setting('lockout_duration_minutes', '30'))
        
        if attempts >= max_attempts:
            locked_until = datetime.now() + timedelta(minutes=lockout_duration)
            cursor.execute(
                "UPDATE users SET locked_until = %s WHERE id = %s",
                (locked_until, user_id)
            )
            logger.warning(f"Account locked due to too many login attempts: {user_id}")
    
    def reset_login_attempts(self, user_id: int, connection):
        """Reset login attempts and unlock account"""
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = %s",
            (user_id,)
        )
    
    def create_user(self, email: str, password: str, plan: str = 'free') -> Optional[int]:
        """
        Create a new user account
        
        Args:
            email: User email address
            password: Plain text password (will be hashed)
            plan: User plan (free, premium, pro)
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            password_hash = self.hash_password(password)
            verification_code = self.generate_verification_code()
            verification_expires = datetime.now() + timedelta(hours=24)
            
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO users (email, password_hash, plan, verification_code, verification_expires)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (email, password_hash, plan, verification_code, verification_expires))
                user_id = cursor.lastrowid
                connection.commit()
                
                # Log user creation
                self.log_audit_event(user_id, 'user_created', details={
                    'email': email, 'plan': plan
                })
                
                logger.info(f"User created successfully: {email}")
                return user_id
                
        except Error as e:
            logger.error(f"Error creating user: {e}")
            return None

    def authenticate_user(self, email: str, password: str, ip_address: str = None) -> Optional[Dict]:
        """
        Authenticate user login
        
        Args:
            email: User email
            password: Plain text password
            ip_address: Client IP for security logging
            
        Returns:
            User data dict if successful, None otherwise
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # Check if user exists and get details
                query = """
                SELECT id, email, password_hash, plan, is_verified, login_attempts, 
                       locked_until, last_login
                FROM users WHERE email = %s
                """
                
                cursor.execute(query, (email,))
                user = cursor.fetchone()
                
                if not user:
                    return None
                
                # Check if account is locked
                if user['locked_until'] and datetime.now() < user['locked_until']:
                    logger.warning(f"Login attempt on locked account: {email}")
                    return None
                
                # Verify password
                if not self.verify_password(password, user['password_hash']):
                    # Increment login attempts
                    self.increment_login_attempts(user['id'], connection)
                    return None
                
                # Reset login attempts on successful login
                self.reset_login_attempts(user['id'], connection)
                
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.now(), user['id'])
                )
                
                connection.commit()
                
                # Log successful login
                self.log_audit_event(user['id'], 'user_login', details={
                    'ip_address': ip_address
                })
                
                return user
                
        except Error as e:
            logger.error(f"Error authenticating user: {e}")
            return None

    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """
        Create a new user session
        
        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session token
        """
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO user_sessions (user_id, session_token, expires_at, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (user_id, session_token, expires_at, ip_address, user_agent))
                connection.commit()
                
                return session_token
                
        except Error as e:
            logger.error(f"Error creating session: {e}")
            return None

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Validate a user session
        
        Args:
            session_token: Session token to validate
            
        Returns:
            User data if session is valid, None otherwise
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT u.id, u.email, u.plan, u.is_verified, s.expires_at
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = %s AND s.expires_at > %s
                """
                
                cursor.execute(query, (session_token, datetime.now()))
                result = cursor.fetchone()
                
                if result:
                    # Update user's last_active
                    cursor.execute(
                        "UPDATE users SET last_active = %s WHERE id = %s",
                        (datetime.now(), result['id'])
                    )
                    connection.commit()
                
                return result
                
        except Error as e:
            logger.error(f"Error validating session: {e}")
            return None

    def verify_user_email(self, email: str, verification_code: str) -> bool:
        """Verify user email with code"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                UPDATE users 
                SET is_verified = TRUE, verification_code = NULL, verification_expires = NULL
                WHERE email = %s AND verification_code = %s AND verification_expires > %s
                """
                
                cursor.execute(query, (email, verification_code, datetime.now()))
                success = cursor.rowcount > 0
                connection.commit()
                
                if success:
                    logger.info(f"Email verified successfully: {email}")
                
                return success
                
        except Error as e:
            logger.error(f"Error verifying email: {e}")
            return False

    def delete_session(self, session_token: str) -> bool:
        """Delete a user session (logout)"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                cursor.execute("DELETE FROM user_sessions WHERE session_token = %s", (session_token,))
                success = cursor.rowcount > 0
                connection.commit()
                
                return success
                
        except Error as e:
            logger.error(f"Error deleting session: {e}")
            return False

    # =============================================================================
    # DYNAMIC CONTENT GENERATION METHODS
    # =============================================================================
    
    def generate_session_id(self, user_id: int) -> str:
        """Generate unique session ID for content generation"""
        timestamp = int(datetime.now().timestamp())
        random_part = secrets.randbelow(10000)
        return f"{user_id}_{timestamp}_{random_part}"

    def create_flashcard(self, user_id: int, question: str, answer: str, topic: str = None,
                        difficulty: str = 'intermediate', source_type: str = 'topic_generation',
                        generation_session: str = None, ai_confidence: float = 0.7) -> Optional[int]:
        """
        Create a new flashcard (dynamically generated)
        
        Args:
            user_id: User ID
            question: Flashcard question
            answer: Flashcard answer
            topic: Topic/subject
            difficulty: Difficulty level
            source_type: How the flashcard was generated
            generation_session: Unique generation session ID
            ai_confidence: AI confidence score
            
        Returns:
            Flashcard ID if successful
        """
        try:
            if not generation_session:
                generation_session = self.generate_session_id(user_id)
            
            variation_seed = secrets.token_hex(8)
            
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO flashcards (
                    user_id, question, answer, topic, difficulty, source_type,
                    generation_session, ai_confidence, variation_seed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    user_id, question, answer, topic, difficulty, source_type,
                    generation_session, ai_confidence, variation_seed
                ))
                
                flashcard_id = cursor.lastrowid
                connection.commit()
                
                logger.info(f"Flashcard created: {flashcard_id}")
                return flashcard_id
                
        except Error as e:
            logger.error(f"Error creating flashcard: {e}")
            return None

    def create_quiz(self, user_id: int, title: str, topic: str = None,
                   difficulty: str = 'mixed', source_type: str = 'topic_generation',
                   time_limit: int = None, passing_score: float = 70.0) -> Optional[int]:
        """
        Create a new quiz (dynamically generated)
        
        Args:
            user_id: User ID
            title: Quiz title
            topic: Quiz topic
            difficulty: Difficulty level
            source_type: How the quiz was generated
            time_limit: Time limit in minutes
            passing_score: Passing score percentage
            
        Returns:
            Quiz ID if successful
        """
        try:
            generation_session = self.generate_session_id(user_id)
            variation_seed = secrets.token_hex(8)
            
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO quizzes (
                    user_id, title, topic, difficulty, source_type,
                    generation_session, variation_seed, time_limit, passing_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    user_id, title, topic, difficulty, source_type,
                    generation_session, variation_seed, time_limit, passing_score
                ))
                
                quiz_id = cursor.lastrowid
                connection.commit()
                
                logger.info(f"Quiz created: {quiz_id}")
                return quiz_id
                
        except Error as e:
            logger.error(f"Error creating quiz: {e}")
            return None

    def add_quiz_question(self, quiz_id: int, question: str, question_type: str,
                         correct_answer: str, options: List = None, explanation: str = None,
                         difficulty: str = 'intermediate', points: int = 1,
                         ai_confidence: float = 0.7) -> Optional[int]:
        """
        Add a question to a quiz (dynamically generated)
        
        Args:
            quiz_id: Quiz ID
            question: Question text
            question_type: Type of question (multiple_choice, true_false, etc.)
            correct_answer: Correct answer
            options: List of options for multiple choice
            explanation: Answer explanation
            difficulty: Question difficulty
            points: Points for correct answer
            ai_confidence: AI confidence score
            
        Returns:
            Question ID if successful
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                # Convert options to JSON if provided
                options_json = json.dumps(options) if options else None
                
                query = """
                INSERT INTO quiz_questions (
                    quiz_id, question, question_type, correct_answer, options,
                    explanation, difficulty, points, ai_confidence
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    quiz_id, question, question_type, correct_answer, options_json,
                    explanation, difficulty, points, ai_confidence
                ))
                
                question_id = cursor.lastrowid
                
                # Update total questions count in quiz
                cursor.execute(
                    "UPDATE quizzes SET total_questions = total_questions + 1 WHERE id = %s",
                    (quiz_id,)
                )
                
                connection.commit()
                
                logger.info(f"Quiz question added: {question_id}")
                return question_id
                
        except Error as e:
            logger.error(f"Error adding quiz question: {e}")
            return None

    def create_generation_session(self, user_id: int, generation_type: str, topic: str = None,
                                 difficulty: str = 'mixed', content_source: str = None,
                                 ai_model: str = 'huggingface', prompt_used: str = None) -> str:
        """Create a generation session record"""
        try:
            session_id = self.generate_session_id(user_id)
            variation_seed = secrets.token_hex(8)
            
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO generation_sessions (
                    user_id, session_id, generation_type, topic, difficulty,
                    content_source, variation_seed, ai_model, prompt_used
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    user_id, session_id, generation_type, topic, difficulty,
                    content_source, variation_seed, ai_model, prompt_used
                ))
                
                connection.commit()
                return session_id
                
        except Error as e:
            logger.error(f"Error creating generation session: {e}")
            return None

    def update_generation_session(self, session_id: str, items_generated: int = None,
                                 generation_time: float = None):
        """Update generation session with completion data"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                updates = []
                params = []
                
                if items_generated is not None:
                    updates.append("items_generated = %s")
                    params.append(items_generated)
                
                if generation_time is not None:
                    updates.append("generation_time = %s")
                    params.append(generation_time)
                
                if updates:
                    params.append(session_id)
                    query = f"UPDATE generation_sessions SET {', '.join(updates)} WHERE session_id = %s"
                    cursor.execute(query, params)
                    connection.commit()
                
        except Error as e:
            logger.error(f"Error updating generation session: {e}")

    # =============================================================================
    # DATA RETRIEVAL METHODS
    # =============================================================================
    
    def get_user_flashcards(self, user_id: int, topic: str = None, limit: int = None) -> List[Dict]:
        """Get user's flashcards with optional filtering"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT id, question, answer, topic, difficulty, times_reviewed,
                       times_correct, mastery_level, created_at
                FROM flashcards
                WHERE user_id = %s
                """
                params = [user_id]
                
                if topic:
                    query += " AND topic = %s"
                    params.append(topic)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting flashcards: {e}")
            return []

    def get_user_quizzes(self, user_id: int, topic: str = None, limit: int = None) -> List[Dict]:
        """Get user's quizzes with optional filtering"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT id, title, topic, difficulty, total_questions,
                       time_limit, passing_score, created_at
                FROM quizzes
                WHERE user_id = %s
                """
                params = [user_id]
                
                if topic:
                    query += " AND topic = %s"
                    params.append(topic)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting quizzes: {e}")
            return []

    def get_quiz_with_questions(self, quiz_id: int, user_id: int = None) -> Optional[Dict]:
        """Get quiz with all its questions"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # Get quiz details
                quiz_query = """
                SELECT id, title, topic, difficulty, total_questions,
                       time_limit, passing_score, created_at
                FROM quizzes
                WHERE id = %s
                """
                params = [quiz_id]
                
                if user_id:
                    quiz_query += " AND user_id = %s"
                    params.append(user_id)
                
                cursor.execute(quiz_query, params)
                quiz = cursor.fetchone()
                
                if not quiz:
                    return None
                
                # Get quiz questions
                questions_query = """
                SELECT id, question, question_type, correct_answer, options,
                       explanation, difficulty, points
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY id
                """
                
                cursor.execute(questions_query, (quiz_id,))
                questions = cursor.fetchall()
                
                # Parse JSON options
                for question in questions:
                    if question['options']:
                        question['options'] = json.loads(question['options'])
                
                quiz['questions'] = questions
                return quiz
                
        except Error as e:
            logger.error(f"Error getting quiz with questions: {e}")
            return None

    def get_user_conversations(self, user_id: int, limit: int = None) -> List[Dict]:
        """Get user's conversations"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT id, title, topic, created_at, updated_at
                FROM conversations
                WHERE user_id = %s
                ORDER BY updated_at DESC
                """
                params = [user_id]
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting conversations: {e}")
            return []

    def get_conversation_messages(self, conversation_id: int, user_id: int = None) -> List[Dict]:
        """Get messages from a conversation"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT m.id, m.content, m.is_user, m.ai_model, m.confidence,
                       m.processing_time, m.timestamp
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.conversation_id = %s
                """
                params = [conversation_id]
                
                if user_id:
                    query += " AND c.user_id = %s"
                    params.append(user_id)
                
                query += " ORDER BY m.timestamp"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []

    def get_user_files(self, user_id: int, processed_only: bool = False) -> List[Dict]:
        """Get user's uploaded files"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT id, filename, original_filename, file_type, file_size,
                       processed, flashcards_generated, quiz_questions_generated,
                       uploaded_at, processed_at
                FROM uploaded_files
                WHERE user_id = %s
                """
                params = [user_id]
                
                if processed_only:
                    query += " AND processed = TRUE"
                
                query += " ORDER BY uploaded_at DESC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting user files: {e}")
            return []

    def get_user_progress(self, user_id: int, topic: str = None) -> List[Dict]:
        """Get user's learning progress"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT topic, total_study_time, flashcards_reviewed, quizzes_completed,
                       average_score, mastery_level, streak_days, last_studied,
                       first_studied, updated_at
                FROM user_progress
                WHERE user_id = %s
                """
                params = [user_id]
                
                if topic:
                    query += " AND topic = %s"
                    params.append(topic)
                
                query += " ORDER BY mastery_level DESC, last_studied DESC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting user progress: {e}")
            return []

    def get_user_study_stats(self, user_id: int, days: int = 30) -> Dict:
        """Get user's study statistics for the last N days"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                since_date = datetime.now() - timedelta(days=days)
                
                # Get study sessions stats
                sessions_query = """
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(time_spent) as total_time,
                    SUM(items_studied) as total_items,
                    SUM(correct_answers) as total_correct,
                    AVG(accuracy) as avg_accuracy
                FROM study_sessions
                WHERE user_id = %s AND started_at >= %s
                """
                
                cursor.execute(sessions_query, (user_id, since_date))
                sessions_stats = cursor.fetchone()
                
                # Get flashcard stats
                flashcards_query = """
                SELECT COUNT(*) as total_flashcards
                FROM flashcards
                WHERE user_id = %s AND created_at >= %s
                """
                
                cursor.execute(flashcards_query, (user_id, since_date))
                flashcards_stats = cursor.fetchone()
                
                # Get quiz stats
                quiz_attempts_query = """
                SELECT 
                    COUNT(*) as total_attempts,
                    AVG(percentage) as avg_score
                FROM quiz_attempts
                WHERE user_id = %s AND started_at >= %s
                """
                
                cursor.execute(quiz_attempts_query, (user_id, since_date))
                quiz_stats = cursor.fetchone()
                
                return {
                    'period_days': days,
                    'sessions': sessions_stats or {},
                    'flashcards': flashcards_stats or {},
                    'quizzes': quiz_stats or {}
                }
                
        except Error as e:
            logger.error(f"Error getting user study stats: {e}")
            return {}

    # =============================================================================
    # STUDY SESSION AND PROGRESS TRACKING
    # =============================================================================
    
    def create_study_session(self, user_id: int, session_type: str, topic: str = None,
                           difficulty_level: str = 'mixed') -> Optional[int]:
        """Create a new study session"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO study_sessions (user_id, session_type, topic, difficulty_level)
                VALUES (%s, %s, %s, %s)
                """
                
                cursor.execute(query, (user_id, session_type, topic, difficulty_level))
                session_id = cursor.lastrowid
                connection.commit()
                
                return session_id
                
        except Error as e:
            logger.error(f"Error creating study session: {e}")
            return None

    def update_study_session(self, session_id: int, items_studied: int = None,
                           correct_answers: int = None, time_spent: int = None,
                           accuracy: float = None):
        """Update study session with progress data"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                updates = []
                params = []
                
                if items_studied is not None:
                    updates.append("items_studied = %s")
                    params.append(items_studied)
                
                if correct_answers is not None:
                    updates.append("correct_answers = %s")
                    params.append(correct_answers)
                
                if time_spent is not None:
                    updates.append("time_spent = %s")
                    params.append(time_spent)
                
                if accuracy is not None:
                    updates.append("accuracy = %s")
                    params.append(accuracy)
                
                if updates:
                    updates.append("ended_at = %s")
                    params.extend([datetime.now(), session_id])
                    
                    query = f"UPDATE study_sessions SET {', '.join(updates)} WHERE id = %s"
                    cursor.execute(query, params)
                    connection.commit()
                
        except Error as e:
            logger.error(f"Error updating study session: {e}")

    def update_flashcard_review(self, flashcard_id: int, correct: bool):
        """Update flashcard review statistics"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                # Get current stats
                cursor.execute(
                    "SELECT times_reviewed, times_correct FROM flashcards WHERE id = %s",
                    (flashcard_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    times_reviewed = result[0] + 1
                    times_correct = result[1] + (1 if correct else 0)
                    mastery_level = times_correct / times_reviewed if times_reviewed > 0 else 0
                    
                    query = """
                    UPDATE flashcards 
                    SET times_reviewed = %s, times_correct = %s, mastery_level = %s,
                        last_reviewed = %s
                    WHERE id = %s
                    """
                    
                    cursor.execute(query, (
                        times_reviewed, times_correct, mastery_level,
                        datetime.now(), flashcard_id
                    ))
                    connection.commit()
                
        except Error as e:
            logger.error(f"Error updating flashcard review: {e}")

    def update_user_progress(self, user_id: int, topic: str, study_time: int = 0,
                           flashcards_reviewed: int = 0, quiz_completed: bool = False,
                           quiz_score: float = None):
        """Update or create user progress for a topic"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                # Check if progress record exists
                cursor.execute(
                    "SELECT id, average_score, quizzes_completed FROM user_progress WHERE user_id = %s AND topic = %s",
                    (user_id, topic)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    updates = ["total_study_time = total_study_time + %s"]
                    params = [study_time]
                    
                    if flashcards_reviewed > 0:
                        updates.append("flashcards_reviewed = flashcards_reviewed + %s")
                        params.append(flashcards_reviewed)
                    
                    if quiz_completed:
                        updates.append("quizzes_completed = quizzes_completed + 1")
                        
                        if quiz_score is not None:
                            # Calculate new average score
                            current_avg = existing[2] or 0
                            quiz_count = existing[1] + 1
                            new_avg = ((current_avg * existing[1]) + quiz_score) / quiz_count
                            updates.append("average_score = %s")
                            params.append(new_avg)
                    
                    updates.append("last_studied = %s")
                    params.extend([datetime.now().date(), user_id, topic])
                    
                    query = f"UPDATE user_progress SET {', '.join(updates)} WHERE user_id = %s AND topic = %s"
                    cursor.execute(query, params)
                    
                else:
                    # Create new progress record
                    query = """
                    INSERT INTO user_progress (
                        user_id, topic, total_study_time, flashcards_reviewed,
                        quizzes_completed, average_score, last_studied
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(query, (
                        user_id, topic, study_time, flashcards_reviewed,
                        1 if quiz_completed else 0,
                        quiz_score if quiz_score is not None else 0.0,
                        datetime.now().date()
                    ))
                
                connection.commit()
                
        except Error as e:
            logger.error(f"Error updating user progress: {e}")

    # =============================================================================
    # QUIZ ATTEMPTS AND SCORING
    # =============================================================================
    
    def create_quiz_attempt(self, quiz_id: int, user_id: int) -> Optional[int]:
        """Create a new quiz attempt"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO quiz_attempts (quiz_id, user_id, answers)
                VALUES (%s, %s, %s)
                """
                
                cursor.execute(query, (quiz_id, user_id, json.dumps({})))
                attempt_id = cursor.lastrowid
                connection.commit()
                
                return attempt_id
                
        except Error as e:
            logger.error(f"Error creating quiz attempt: {e}")
            return None

    def submit_quiz_attempt(self, attempt_id: int, answers: Dict, score: float,
                          percentage: float, time_taken: int = None) -> bool:
        """Submit completed quiz attempt"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                UPDATE quiz_attempts 
                SET answers = %s, score = %s, percentage = %s, time_taken = %s,
                    completed_at = %s
                WHERE id = %s
                """
                
                cursor.execute(query, (
                    json.dumps(answers), score, percentage, time_taken,
                    datetime.now(), attempt_id
                ))
                
                success = cursor.rowcount > 0
                connection.commit()
                
                return success
                
        except Error as e:
            logger.error(f"Error submitting quiz attempt: {e}")
            return False

    def get_quiz_attempts(self, user_id: int, quiz_id: int = None) -> List[Dict]:
        """Get quiz attempts for a user"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT qa.id, qa.quiz_id, q.title as quiz_title, qa.score,
                       qa.percentage, qa.time_taken, qa.started_at, qa.completed_at
                FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id
                WHERE qa.user_id = %s
                """
                params = [user_id]
                
                if quiz_id:
                    query += " AND qa.quiz_id = %s"
                    params.append(quiz_id)
                
                query += " ORDER BY qa.started_at DESC"
                
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except Error as e:
            logger.error(f"Error getting quiz attempts: {e}")
            return []

    # =============================================================================
    # FILE UPLOAD MANAGEMENT
    # =============================================================================
    
    def create_uploaded_file(self, user_id: int, filename: str, original_filename: str,
                           file_type: str, file_size: int, file_path: str) -> Optional[int]:
        """Record an uploaded file"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO uploaded_files (
                    user_id, filename, original_filename, file_type,
                    file_size, file_path
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    user_id, filename, original_filename, file_type,
                    file_size, file_path
                ))
                
                file_id = cursor.lastrowid
                connection.commit()
                
                return file_id
                
        except Error as e:
            logger.error(f"Error creating uploaded file record: {e}")
            return None

    def update_file_processing(self, file_id: int, content: str = None,
                             content_summary: str = None, processed: bool = False,
                             processing_error: str = None, flashcards_generated: int = 0,
                             quiz_questions_generated: int = 0):
        """Update file processing status and results"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                UPDATE uploaded_files 
                SET content = %s, content_summary = %s, processed = %s,
                    processing_error = %s, flashcards_generated = %s,
                    quiz_questions_generated = %s, processed_at = %s
                WHERE id = %s
                """
                
                cursor.execute(query, (
                    content, content_summary, processed, processing_error,
                    flashcards_generated, quiz_questions_generated,
                    datetime.now() if processed else None, file_id
                ))
                
                connection.commit()
                
        except Error as e:
            logger.error(f"Error updating file processing: {e}")

    # =============================================================================
    # CONVERSATION AND MESSAGING
    # =============================================================================
    
    def create_conversation(self, user_id: int, title: str = 'New Conversation',
                          topic: str = None) -> Optional[int]:
        """Create a new conversation"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO conversations (user_id, title, topic)
                VALUES (%s, %s, %s)
                """
                
                cursor.execute(query, (user_id, title, topic))
                conversation_id = cursor.lastrowid
                connection.commit()
                
                return conversation_id
                
        except Error as e:
            logger.error(f"Error creating conversation: {e}")
            return None

    def add_message(self, conversation_id: int, content: str, is_user: bool,
                   ai_model: str = 'huggingface', confidence: float = None,
                   processing_time: float = None) -> Optional[int]:
        """Add a message to a conversation"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO messages (
                    conversation_id, content, is_user, ai_model,
                    confidence, processing_time
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    conversation_id, content, is_user, ai_model,
                    confidence, processing_time
                ))
                
                message_id = cursor.lastrowid
                
                # Update conversation updated_at
                cursor.execute(
                    "UPDATE conversations SET updated_at = %s WHERE id = %s",
                    (datetime.now(), conversation_id)
                )
                
                connection.commit()
                return message_id
                
        except Error as e:
            logger.error(f"Error adding message: {e}")
            return None

    # =============================================================================
    # UTILITY AND SETTINGS METHODS
    # =============================================================================
    
    def get_setting(self, key: str, default: str = None) -> str:
        """Get application setting value"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                cursor.execute(
                    "SELECT setting_value FROM app_settings WHERE setting_key = %s",
                    (key,)
                )
                result = cursor.fetchone()
                
                return result[0] if result else default
                
        except Error as e:
            logger.error(f"Error getting setting: {e}")
            return default

    def set_setting(self, key: str, value: str, description: str = None) -> bool:
        """Set application setting value"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO app_settings (setting_key, setting_value, description)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                setting_value = VALUES(setting_value),
                description = COALESCE(VALUES(description), description)
                """
                
                cursor.execute(query, (key, value, description))
                connection.commit()
                
                return True
                
        except Error as e:
            logger.error(f"Error setting application setting: {e}")
            return False

    def log_audit_event(self, user_id: int = None, action: str = '', resource_type: str = None,
                       resource_id: int = None, ip_address: str = None,
                       user_agent: str = None, details: Dict = None):
        """Log an audit event"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO audit_logs (
                    user_id, action, resource_type, resource_id,
                    ip_address, user_agent, details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    user_id, action, resource_type, resource_id,
                    ip_address, user_agent, json.dumps(details) if details else None
                ))
                
                connection.commit()
                
        except Error as e:
            logger.error(f"Error logging audit event: {e}")

    def check_rate_limit(self, ip_address: str, endpoint: str, limit: int = 100,
                        window_minutes: int = 60) -> bool:
        """Check if IP address has exceeded rate limit for endpoint"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                window_start = datetime.now() - timedelta(minutes=window_minutes)
                
                # Get or create rate limit record
                cursor.execute(
                    """
                    INSERT INTO rate_limits (ip_address, endpoint, window_start)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    request_count = CASE 
                        WHEN window_start < %s THEN 1
                        ELSE request_count + 1
                    END,
                    window_start = CASE
                        WHEN window_start < %s THEN %s
                        ELSE window_start
                    END
                    """,
                    (ip_address, endpoint, datetime.now(), window_start, window_start, datetime.now())
                )
                
                # Check current count
                cursor.execute(
                    "SELECT request_count, is_blocked FROM rate_limits WHERE ip_address = %s AND endpoint = %s",
                    (ip_address, endpoint)
                )
                result = cursor.fetchone()
                
                if result:
                    count, is_blocked = result
                    
                    # Block if over limit
                    if count > limit and not is_blocked:
                        cursor.execute(
                            "UPDATE rate_limits SET is_blocked = TRUE WHERE ip_address = %s AND endpoint = %s",
                            (ip_address, endpoint)
                        )
                        is_blocked = True
                    
                    connection.commit()
                    return not is_blocked and count <= limit
                
                return True
                
        except Error as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error

    def cleanup_expired_sessions(self):
        """Clean up expired sessions and other old data"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                # Remove expired sessions
                cursor.execute("DELETE FROM user_sessions WHERE expires_at < %s", (datetime.now(),))
                expired_sessions = cursor.rowcount
                
                # Clean up old rate limit records
                old_rate_limits = datetime.now() - timedelta(hours=24)
                cursor.execute("DELETE FROM rate_limits WHERE window_start < %s", (old_rate_limits,))
                old_rate_records = cursor.rowcount
                
                # Clean up old audit logs (keep last 90 days)
                old_audit_date = datetime.now() - timedelta(days=90)
                cursor.execute("DELETE FROM audit_logs WHERE timestamp < %s", (old_audit_date,))
                old_audit_logs = cursor.rowcount
                
                connection.commit()
                
                logger.info(f"Cleanup completed: {expired_sessions} sessions, {old_rate_records} rate records, {old_audit_logs} audit logs")
                
        except Error as e:
            logger.error(f"Error during cleanup: {e}")

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                stats = {}
                
                # Count records in main tables
                tables = [
                    'users', 'user_sessions', 'conversations', 'messages',
                    'flashcards', 'quizzes', 'quiz_questions', 'quiz_attempts',
                    'uploaded_files', 'study_sessions', 'user_progress',
                    'generation_sessions', 'audit_logs'
                ]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                return stats
                
        except Error as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

    def search_content(self, user_id: int, query: str, content_type: str = 'all', limit: int = 20) -> Dict:
        """
        Search through user's content (flashcards, conversations, files)
        
        Args:
            user_id: User ID
            query: Search query
            content_type: 'flashcards', 'conversations', 'files', or 'all'
            limit: Maximum results per category
            
        Returns:
            Dictionary with search results by category
        """
        try:
            results = {}
            
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                if content_type in ['flashcards', 'all']:
                    # Search flashcards
                    flashcard_query = """
                    SELECT id, question, answer, topic, created_at,
                           MATCH(question, answer) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
                    FROM flashcards
                    WHERE user_id = %s AND MATCH(question, answer) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    ORDER BY relevance DESC
                    LIMIT %s
                    """
                    
                    cursor.execute(flashcard_query, (query, user_id, query, limit))
                    results['flashcards'] = cursor.fetchall()
                
                if content_type in ['conversations', 'all']:
                    # Search conversation messages
                    message_query = """
                    SELECT m.id, m.content, m.is_user, m.timestamp, c.title as conversation_title,
                           MATCH(m.content) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = %s AND MATCH(m.content) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    ORDER BY relevance DESC
                    LIMIT %s
                    """
                    
                    cursor.execute(message_query, (query, user_id, query, limit))
                    results['conversations'] = cursor.fetchall()
                
                if content_type in ['files', 'all']:
                    # Search file content
                    file_query = """
                    SELECT id, original_filename, content_summary, uploaded_at,
                           MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
                    FROM uploaded_files
                    WHERE user_id = %s AND processed = TRUE 
                    AND MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    ORDER BY relevance DESC
                    LIMIT %s
                    """
                    
                    cursor.execute(file_query, (query, user_id, query, limit))
                    results['files'] = cursor.fetchall()
                
                return results
                
        except Error as e:
            logger.error(f"Error searching content: {e}")
            return {}

    def get_user_plan_limits(self, plan: str) -> Dict:
        """Get usage limits for a user plan"""
        limits = {
            'free': {
                'daily_chat_messages': int(self.get_setting('free_plan_daily_limit_chat', '10')),
                'daily_flashcard_generations': int(self.get_setting('free_plan_daily_limit_flashcards', '3')),
                'daily_file_uploads': int(self.get_setting('free_plan_daily_limit_uploads', '1')),
                'max_file_size_mb': int(self.get_setting('max_file_size_mb', '5')),
                'max_flashcards_per_generation': int(self.get_setting('max_flashcards_per_generation', '5')),
                'max_quiz_questions_per_generation': int(self.get_setting('max_quiz_questions_per_generation', '5'))
            },
            'premium': {
                'daily_chat_messages': 100,
                'daily_flashcard_generations': 20,
                'daily_file_uploads': 10,
                'max_file_size_mb': int(self.get_setting('max_file_size_mb', '10')),
                'max_flashcards_per_generation': int(self.get_setting('max_flashcards_per_generation', '10')),
                'max_quiz_questions_per_generation': int(self.get_setting('max_quiz_questions_per_generation', '8'))
            },
            'pro': {
                'daily_chat_messages': -1,  # Unlimited
                'daily_flashcard_generations': -1,
                'daily_file_uploads': -1,
                'max_file_size_mb': 50,
                'max_flashcards_per_generation': 20,
                'max_quiz_questions_per_generation': 15
            }
        }
        
        return limits.get(plan, limits['free'])

    def check_user_daily_usage(self, user_id: int, action: str) -> Dict:
        """
        Check user's daily usage for a specific action
        
        Args:
            user_id: User ID
            action: 'chat', 'flashcard_generation', 'file_upload'
            
        Returns:
            Dictionary with usage info: {'used': int, 'limit': int, 'can_proceed': bool}
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                
                # Get user plan
                cursor.execute("SELECT plan FROM users WHERE id = %s", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return {'used': 0, 'limit': 0, 'can_proceed': False}
                
                plan = result[0]
                limits = self.get_user_plan_limits(plan)
                
                today = datetime.now().date()
                used = 0
                
                if action == 'chat':
                    # Count messages from user today
                    query = """
                    SELECT COUNT(*)
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = %s AND m.is_user = TRUE 
                    AND DATE(m.timestamp) = %s
                    """
                    cursor.execute(query, (user_id, today))
                    used = cursor.fetchone()[0]
                    limit = limits['daily_chat_messages']
                
                elif action == 'flashcard_generation':
                    # Count flashcard generation sessions today
                    query = """
                    SELECT COUNT(DISTINCT generation_session)
                    FROM flashcards
                    WHERE user_id = %s AND DATE(created_at) = %s
                    """
                    cursor.execute(query, (user_id, today))
                    used = cursor.fetchone()[0]
                    limit = limits['daily_flashcard_generations']
                
                elif action == 'file_upload':
                    # Count file uploads today
                    query = """
                    SELECT COUNT(*)
                    FROM uploaded_files
                    WHERE user_id = %s AND DATE(uploaded_at) = %s
                    """
                    cursor.execute(query, (user_id, today))
                    used = cursor.fetchone()[0]
                    limit = limits['daily_file_uploads']
                
                else:
                    limit = 0
                
                can_proceed = limit == -1 or used < limit
                
                return {
                    'used': used,
                    'limit': limit,
                    'can_proceed': can_proceed,
                    'plan': plan
                }
                
        except Error as e:
            logger.error(f"Error checking daily usage: {e}")
            return {'used': 0, 'limit': 0, 'can_proceed': False}

    def close_connection_pool(self):
        """Close the connection pool when shutting down"""
        try:
            if self.connection_pool:
                # Close all connections in the pool
                logger.info("Closing database connection pool")
        except Exception as e:
            logger.error(f"Error closing connection pool: {e}")


# =============================================================================
# EXAMPLE USAGE AND SETUP
# =============================================================================

def setup_brainypal_database():
    """
    Example setup function for BrainyPal database
    Run this once to set up the database
    """
    
    # Database configuration
    config = {
        'host': 'localhost',
        'database': 'brainypal_db',
        'user': 'brainypal_app',
        'password': 'BrainyPal2024!SecureApp#',
        'pool_name': 'brainypal_pool',
        'pool_size': 10
    }
    
    try:
        # Initialize database manager
        db = DatabaseManager(config)
        
        # Create the complete schema
        db.create_database_schema()
        
        print("✅ BrainyPal database setup completed successfully!")
        print("📊 Database includes:")
        print("   - User management and authentication")
        print("   - Dynamic flashcard generation")
        print("   - Dynamic quiz creation")
        print("   - File upload and processing")
        print("   - Conversation and chat history")
        print("   - Study sessions and progress tracking")
        print("   - Audit logging and rate limiting")
        print("   - Application settings management")
        
        # Get database statistics
        stats = db.get_database_stats()
        print(f"\n📈 Database Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
        return db
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return None


if __name__ == "__main__":
    # Run database setup
    database = setup_brainypal_database()
    
    if database:
        # Example usage
        print("\n🚀 Ready for BrainyPal application!")
        print("Use the DatabaseManager instance to:")
        print("- Create users: db.create_user(email, password)")
        print("- Generate flashcards: db.create_flashcard(user_id, question, answer)")
        print("- Create quizzes: db.create_quiz(user_id, title)")
        print("- Track progress: db.update_user_progress(user_id, topic)")
        print("- And much more!")