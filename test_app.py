from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)

# Configure CORS properly
CORS(app, 
     origins=["http://127.0.0.1:5500", "http://localhost:5500"],  # Add your frontend origins
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"]
)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "message": "Backend is running"
    })

# Mock authentication endpoints for testing
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # Mock authentication logic (replace with real logic)
        if email and password:
            if email == 'test@example.com' and password == 'test123':
                return jsonify({
                    "status": "success",
                    "message": "Login successful",
                    "access_token": "mock_token_12345",
                    "user": {"email": email, "name": "Test User"}
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Invalid credentials"
                }), 401
        else:
            return jsonify({
                "status": "error",
                "message": "Email and password required"
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        # Mock registration logic
        if email and password and name:
            return jsonify({
                "status": "success",
                "message": "Registration successful",
                "user": {"email": email, "name": name}
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Email, password, and name required"
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/documents/upload', methods=['POST', 'OPTIONS'])
def upload_document():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    try:
        # Check for authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Authorization token required"
            }), 401
        
        # Check for file
        if 'file' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No file uploaded"
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "status": "error",
                "message": "No file selected"
            }), 400
        
        # Mock file processing
        return jsonify({
            "status": "success",
            "message": "File uploaded successfully",
            "filename": file.filename,
            "size": len(file.read()) if file else 0,
            "document_id": "doc_12345"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/ai/analyze', methods=['POST', 'OPTIONS'])
def ai_analyze():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    
    try:
        # Check for authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                "status": "error",
                "message": "Authorization token required"
            }), 401
        
        data = request.get_json()
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({
                "status": "error",
                "message": "Text is required for analysis"
            }), 400
        
        # Mock AI analysis
        return jsonify({
            "status": "success",
            "message": "AI analysis completed",
            "analysis": {
                "text_length": len(text),
                "word_count": len(text.split()),
                "sentiment": "positive",
                "summary": f"This text contains {len(text.split())} words about: {text[:50]}...",
                "key_topics": ["technology", "innovation", "development"]
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("Starting BrainyPal Test Server...")
    print("Available endpoints:")
    print("- GET  /api/health")
    print("- POST /api/auth/login")
    print("- POST /api/auth/register") 
    print("- POST /api/documents/upload")
    print("- POST /api/ai/analyze")
    app.run(debug=True, host='127.0.0.1', port=5000)