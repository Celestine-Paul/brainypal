# BrainyPal Flask Configuration
# config.py

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Basic Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret key here'
    
    # MySQL Database configuration
    # Format: mysql://username:password@localhost/database_name
import os

class Config:
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_password")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "your_db_name")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}"
        f"@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DATABASE}"
    )
    
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'echo': False  # Set to True for SQL debugging
    }
    
    # JWT Configuration
JWT_SECRET_KEY = ' os.getenv("JWT_KEY")'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
JWT_ALGORITHM = 'HS256'
    
    # File Upload Settings
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'md', 'rtf'}
    
    # AI Service Configuration
HUGGINGFACE_API_TOKEN=os.getenv("HF_TOKEN")
TRANSFORMERS_CACHE='/path/to/transformers/cache'
    
    # paystack Payment Configuration
PAYSTACK_SECRET_KEY=os.getenv("paystack_key")
PAYSTACK_PUBLIC_KEY=os.getenv("PAYSTACK_KEY")
PAYSTACK_WEBHOOK_SECRET=os.getenv("paystack_key")

    
    # Application Settings
APP_NAME = 'BrainyPal'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'AI-powered study companion for smarter learning'
    
    # CORS Settings
CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5500',      # for your Live Server setup
        'https://brainypal.com'    
    ]
    
    # Email Configuration (for notifications and password reset)
MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com' 
MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'email here' 
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'email password here'
MAIL_DEFAULT_SENDER = os.environ.get('noreply@brainypal.com') or MAIL_USERNAME
    
    # Redis Configuration (for caching and sessions)
REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Rate Limiting
RATELIMIT_STORAGE_URL = REDIS_URL
RATELIMIT_DEFAULT = "100 per hour"  # Default rate limit
    
    # Free tier limits
FREE_TIER_LIMITS = {
        'daily_generations': 5,
        'max_flashcards_per_generation': 10,
        'max_questions_per_generation': 5,
        'max_file_size_mb': 5,
        'max_files_per_upload': 3
    }
    
    # Premium tier limits
PREMIUM_TIER_LIMITS = {
        'daily_generations': -1,  # Unlimited
        'max_flashcards_per_generation': 50,
        'max_questions_per_generation': 25,
        'max_file_size_mb': 25,
        'max_files_per_upload': 10
    }
    
    # Pro tier limits
PRO_TIER_LIMITS = {
        'daily_generations': -1,  # Unlimited
        'max_flashcards_per_generation': 100,
        'max_questions_per_generation': 50,
        'max_file_size_mb': 50,
        'max_files_per_upload': 20
    }
    
    # Logging Configuration 
LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
LOG_FILE = os.environ.get('LOG_FILE') or 'brainypal.log'
    
    # Security Settings
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Use local MySQL for development
    SQLALCHEMY_DATABASE_URI = (
         f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    # Relaxed CORS for development
    CORS_ORIGINS = ['*']
    
    # paystack sandbox for development
    PAYSTACK_BASE_URL = 'https://api.paystack.com'
    
    # Development logging
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'pool_recycle': 120,
        'pool_pre_ping': True,
        'echo': True  # Show SQL queries in development
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production MySQL configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'mysql+pymysql://{Config.MYSQL_USER}:{Config.MYSQL_PASSWORD}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DATABASE}'
    
    # Production paystack
    PAYSTACK_BASE_URL = 'https://api.paystack.com'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # SSL/TLS settings
    PREFERRED_URL_SCHEME = 'https'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Shorter token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    
    # Mock API keys for testing
    HUGGINGFACE_API_KEY = 'test_key'
    PAYSTACK_PUBLISHABLE_KEY = 'test_publishable_key'
    PAYSTACK_SECRET_KEY = 'test_secret_key'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Environment-specific settings
def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# Database connection string builder
def build_mysql_uri(user, password, host, port, database, **kwargs):
    """Build MySQL connection URI with additional parameters"""
    base_uri = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
    
    if kwargs:
        params = '&'.join([f'{k}={v}' for k, v in kwargs.items()])
        base_uri += f'?{params}'
    
    return base_uri

# Validation functions
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check required environment variables
    required_vars = [
        'SECRET_KEY',
        'MYSQL_USER',
        'MYSQL_PASSWORD',
        'MYSQL_DATABASE',
        'HUGGINGFACE_API_KEY',
        'PAYSTACK_PUBLISHABLE_KEY',
        'PAYSTACK_SECRET_KEY'
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            errors.append(f'Missing required environment variable: {var}')
    
    # Check MySQL connection parameters
    mysql_params = ['MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_HOST', 'MYSQL_DATABASE']
    for param in mysql_params:
        value = os.environ.get(param)
        if not value or value.strip() == '':
            errors.append(f'MySQL parameter {param} is empty or not set')
    
    # Validate API keys format
    hf_key = os.environ.get('HUGGINGFACE_API_KEY', '')
    if hf_key and not hf_key.startswith('hf_'):
        errors.append('Hugging Face API key should start with "hf_"')
    
    paystack_pub = os.environ.get('paystack_PUBLISHABLE_KEY', '')
    if paystack_pub and not paystack_pub.startswith('ISPubKey_'):
        errors.append('paystack publishable key should start with "ISPubKey_"')
    
    paystack_secret = os.environ.get('PAYSTACK_SECRET_KEY', '')
    if paystack_secret and not paystack_secret.startswith('ISSecretKey_'):
        errors.append('paystack secret key should start with "ISSecretKey_"')
    
    return errors

# Initialize configuration
def init_config(app):
    """Initialize Flask app with configuration"""
    config_name = os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Validate configuration
    validation_errors = validate_config()
    if validation_errors:
        print("Configuration validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app

# Example .env file content for reference
ENV_EXAMPLE = """
# BrainyPal Environment Variables
# Copy this to .env file and update with your actual values

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key

# MySQL Database Configuration
MYSQL_USER=brainypal_user
MYSQL_PASSWORD=your_secure_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=brainypal_db

# Hugging Face AI Configuration
HUGGINGFACE_API_KEY=hf_your_huggingface_api_key_here

# paystack Payment Configuration (Kenya)
paystack_PUBLISHABLE_KEY=ISPubKey_test_your_publishable_key_here
paystack_SECRET_KEY=ISSecretKey_test_your_secret_key_here
paystack_WEBHOOK_SECRET=your_webhook_secret_key

# Email Configuration (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis Configuration (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Production settings (set these in production)
DATABASE_URL=mysql+pymysql://user:password@host:port/database
SESSION_COOKIE_SECURE=true
"""

# Save example .env file
def create_env_example():
    """Create example .env file"""
    with open('.env.example', 'w') as f:
        f.write(ENV_EXAMPLE)
    print("Created .env.example file. Copy to .env and update with your values.")

if __name__ == '__main__':
    create_env_example()
    print("Configuration module loaded successfully!")
    
    # Print current configuration status
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"MySQL Host: {os.environ.get('MYSQL_HOST', 'localhost')}")
    print(f"MySQL Database: {os.environ.get('MYSQL_DATABASE', 'brainypal_db')}")
    
    # Validate configuration
    errors = validate_config()
    if errors:
        print("\nConfiguration Issues:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration looks good!")