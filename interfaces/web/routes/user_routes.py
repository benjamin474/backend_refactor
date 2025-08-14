from flask import Blueprint, request, jsonify
import re
from flask_jwt_extended import jwt_required, get_jwt_identity
from service.auth_service import AuthService
from domain.models.user import User

auth_service = AuthService()
user_bp = Blueprint('user', __name__)


# test route
@user_bp.route('/', methods=['GET'])
def home():
    return "Hello, user!"


@user_bp.route('/register', methods=['POST', 'OPTIONS'])
def register_user():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    if not all(key in data for key in ('username', 'email', 'password')):
        return jsonify({'error': 'All fields are required'}), 400
    if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', data['email']) is None:
        return jsonify({"message": "Email格式不正確"}), 400
    response = auth_service.register_user(data['username'], data['email'], data['password'])
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/login', methods=['POST', 'OPTIONS'])
def login_user():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    if not all(key in data for key in ('email', 'password')):
        return jsonify({'error': 'Email and password are required'}), 400
    
    response = auth_service.login_user(data['email'], data['password'])
    if response['status'] == 'success':
        # Create a User instance from the response
        user_instance = User(
            user_id=response['user']['user_id'],
            username=response['user']['username'],
            email=response['user']['email'],
            password=response['user']['password'],  # Ensure this is hashed in production
            created_at=response['user'].get('created_at'),
            workspace_ids=response['user'].get('workspace_ids', [])
        )
        
        # Generate JWT for the user
        jwt_token = auth_service.createjwt(user_instance)
        response['jwt'] = jwt_token
    
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/user/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    if 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    response = auth_service.forgot_password(data['email'])
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/user/<email>/update-password', methods=['POST'])
def update_password(email):
    data = request.json
    if 'password' not in data:
        return jsonify({'error': 'Password is required'}), 400
    response = auth_service.update_password(email, data['password'])
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/<user_id>', methods=['GET'])
def get_user_workspaces(user_id):
    response = auth_service.get_user(user_id)
    # create jwt token
    user_instance = User(
        user_id=response['user']['user_id'],
        username=response['user']['username'],
        email=response['user']['email'],
        password=response['user']['password'],  # Ensure this is hashed in production
        created_at=response['user'].get('created_at'),
        workspace_ids=response['user'].get('workspace_ids', [])
    )
    jwt_token = auth_service.createjwt(user_instance)
    response['jwt'] = jwt_token
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/email/<email>', methods=['GET'])
@jwt_required()
def get_user_by_email(email):
    # 使用 flask_jwt_extended 的 get_jwt_identity 提取 identity
    user_id = get_jwt_identity()
    print(f"Extracted user_id from JWT: {user_id}")  # 調試用
    if not user_id:
        return jsonify({"error": "Invalid or missing token"}), 401

    # 調用服務層獲取用戶信息
    response = auth_service.get_user_by_email(email)
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/<user_id>/workspace/<workspace_id>', methods=['GET'])
def add_workspace_to_user(user_id, workspace_id):
    response = auth_service.add_workspace_to_user(user_id, workspace_id)
    return jsonify(response), 200 if response['status'] == 'success' else 400

@user_bp.route('/<user_id>/workspace/<workspace_id>', methods=['DELETE'])
def remove_workspace_from_user(user_id, workspace_id):
    response = auth_service.remove_workspace_from_user(user_id, workspace_id)
    return jsonify(response), 200 if response['status'] == 'success' else 400




    