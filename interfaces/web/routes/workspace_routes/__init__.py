from flask import Blueprint, request, jsonify
import re
from service.workspace_service import WorkspaceService
from .analysis_routes import analysis_bp  # 引入 analysis_routes

workspace_service = WorkspaceService()
workspace_bp = Blueprint('workspace', __name__)

# 註冊 analysis 子路由
workspace_bp.register_blueprint(analysis_bp, url_prefix='/<workspace_id>/analysis')

@workspace_bp.route('/', methods=['GET', 'OPTIONS'])
def get_workspaces():
    if request.method == 'OPTIONS':
        return '', 200
    workspaces = workspace_service.get_workspaces()
    return jsonify([workspace.to_dict() for workspace in workspaces]), 200

@workspace_bp.route('/', methods=['POST', 'OPTIONS'])
def create_workspace():
    if request.method == 'OPTIONS':
        return '', 200
    data = request.json
    if 'name' not in data:
        return jsonify({'error': 'Workspace name is required'}), 400
    if not re.match("^[a-zA-Z0-9_]*$", data['name']):
        return jsonify({"message": "工作區名稱僅可包含大小寫英文字母、數字、底線。其餘符號皆不符合規則。"}), 400
    response, status_code = workspace_service.create_workspace(data['name'])
    return jsonify(response), status_code

@workspace_bp.route('/<workspace_id>', methods=['GET', 'OPTIONS'])
def get_workspace(workspace_id):
    if request.method == 'OPTIONS':
        return '', 200
    workspace = workspace_service.get_workspace(workspace_id)
    if workspace:
        return jsonify(workspace.to_dict()), 200
    return jsonify({'error': 'Workspace not found'}), 404

@workspace_bp.route('/<workspace_id>', methods=['DELETE'])
def delete_workspace(workspace_id):
    result = workspace_service.delete_workspace(workspace_id)
    if result.deleted_count == 1:
        return '', 204
    return jsonify({'error': 'Workspace not found'}), 404

# request.json = {"file": [{ "name": "", "content": "" },{ "name": "", "content": "" }, ... ] }
@workspace_bp.route('/<workspace_id>/files', methods=['PUT'])  # Changed to PUT
def add_file_to_workspace(workspace_id):
    data = request.json
    if 'file' not in data or not isinstance(data['file'], list):
        return jsonify({'error': 'File data with name and content is required'}), 400

    for file in data['file']:
        if 'name' not in file or 'content' not in file:
            return jsonify({'error': 'Each file must have a name and content'}), 400

        file_data = {
            'name': file['name'],
            'content': file['content']
        }

        result = workspace_service.add_file_to_workspace(workspace_id, file_data)
        if not result:
            return jsonify({'error': 'Workspace not found'}), 404

    return '', 204

@workspace_bp.route('/<workspace_id>/files/<file_name>', methods=['DELETE'])
def remove_file_from_workspace(workspace_id, file_name):
    result = workspace_service.remove_file_from_workspace(workspace_id, file_name)
    if result:
        return '', 204
    return jsonify({'error': 'Workspace not found'}), 404