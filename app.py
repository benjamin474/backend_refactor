from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from interfaces.web.routes.__init__ import register_blueprints, bp as main_bp
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

app = Flask(__name__)

# 更完整的 CORS 配置
CORS(app, 
     origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

# Register the Blueprint
app.register_blueprint(main_bp)

# Register additional Blueprints
register_blueprints(app)

load_dotenv()  # 確保載入環境變數
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = 'your-secret-key-here'  # 備用密鑰
app.config['JWT_SECRET_KEY'] = SECRET_KEY
jwt = JWTManager(app)

# 處理 OPTIONS 請求 - 增強版
@app.before_request
def handle_options_request():
    if request.method == 'OPTIONS':
        response = make_response()
        origin = request.headers.get('Origin')
        allowed_origins = ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
            
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'
        response.status_code = 200
        return response

# 在每個響應後添加 CORS headers
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = ["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
        
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5001)



