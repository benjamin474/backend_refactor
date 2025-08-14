import json
import os
from unittest import result
from flask import Blueprint, request, jsonify
from infrastructure.repositories.workspaceRepo import WorkspaceRepo
from service.keyword_analysis import KeywordAnalysis
from service.author_analysis import AuthorAnalysis
from service.reference_analysis import ReferenceAnalysis
from service.field_analysis import FieldAnalysis
from service.university_analysis import InstitutionAnalysis
from service.country_analysis import CountryAnalysis
import uuid
from datetime import datetime
import base64

class WorkspaceService:
    def __init__(self):
        self.repo = WorkspaceRepo()

    def get_workspaces(self):
        return self.repo.get_workspaces()

    def get_user_workspaces(self, user_id):
        """批量獲取用戶的所有工作區詳情"""
        from service.auth_service import AuthService
        auth_service = AuthService()
        
        # 獲取用戶的工作區ID列表
        user_response = auth_service.get_user(user_id)
        if not user_response or user_response.get('status') != 'success':
            return []
        
        user_data = user_response.get('user', {})
        workspace_ids = user_data.get('workspace_ids', [])
        
        # 批量獲取工作區詳情
        workspaces = []
        for workspace_id in workspace_ids:
            workspace = self.repo.get_workspace(workspace_id)
            if workspace:
                workspaces.append(workspace.to_dict())
        
        return workspaces

    def create_workspace(self, name):
        if self.repo.workspace_name_exists(name):
            return {"status": "error", "message": "The name already exists"}, 400
        workspace_id = str(uuid.uuid4())
        workspace = self.repo.create_workspace(id=workspace_id, name=name)
        if workspace:
            return {"status": "success", "message": "Workspace created successfully", "workspace": workspace.to_dict()}, 201
        return {"status": "error", "message": "Failed to create workspace"}, 500

    def get_workspace(self, workspace_id):
        return self.repo.get_workspace(workspace_id)

    def delete_workspace(self, workspace_id):
        return self.repo.delete_workspace(workspace_id)

    def add_file_to_workspace(self, workspace_id, file):
        # Decode the Base64-encoded content
        if 'content' in file:
            file['content'] = base64.b64decode(file['content']).decode('utf-8')
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            workspace.add_file(file)
            update_result = self.repo.update_workspace(workspace)
            return update_result.modified_count > 0
        return False

    def remove_file_from_workspace(self, workspace_id, file_name):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            workspace.remove_file(file_name)
            update_result = self.repo.update_workspace(workspace)
            return update_result.modified_count > 0
        return False

    def get_analysis(self, workspace_id):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            if workspace.latest_result:
                return workspace.latest_result       
        return None

    def save_analysis_to_file(self, workspace_id, analysis):
        # 假設結果存儲為 JSON 格式
        file_path = f'temp/analysis_{workspace_id}.json'

        # 確保 temp 資料夾存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 將結果保存為 JSON 檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        return file_path

    def keyword_analysis(self, workspace_id, keyword):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, conditionCount, start, end, results = KeywordAnalysis.keywordEachYear(files, files, keyword)
            workspace.latest_result = {
                'type': 'keyword_analysis',
                'count': count,
                'conditionCount': conditionCount,
                'start': start,
                'end': end,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def keyword_analysis_year(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, conditionCount, results = KeywordAnalysis.year(files, files, start, end, threshold)
            workspace.latest_result = {
                'type': 'keyword_analysis_year',
                'count': count,
                'conditionCount': conditionCount,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def keyword_analysis_occurence(self, workspace_id, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            titleCount, results = KeywordAnalysis.keywordOccurence(files, files, threshold)
            workspace.latest_result = {
                'type': 'keyword_analysis_occurence',
                'titleCount': titleCount,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    # 根據年份區間對作者做分析（看年份區間內作者發表了幾篇）
    def author_analysis_year(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, conditionCount, results = AuthorAnalysis.author(files, files, start, end, threshold)
            workspace.latest_result = {
                'type': 'author_analysis',
                'count': count,
                'conditionCount': conditionCount,
                'conditionCount': conditionCount,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    # 根據引用次數做分析
    def reference_analysis(self, workspace_id, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, results = ReferenceAnalysis.get_referencesInfo(files, files, threshold)
            workspace.latest_result = {
                'type': 'reference_analysis',
                'count': count,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def field_analysis(self, workspace_id, field):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, conditionCount, start, end, results = FieldAnalysis.fieldField(files, files, field)
            workspace.latest_result = {
                'type': 'field_analysis',
                'count': count,
                'conditionCount': conditionCount,
                'start': start,
                'end': end,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def field_analysis_year(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, conditionCount, results = FieldAnalysis.fieldEachYear(files, files, start, end, threshold)
            workspace.latest_result = {
                'type': 'field_analysis_year',
                'count': count,
                'conditionCount': conditionCount,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def field_analysis_occurence(self, workspace_id, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            titleCount, results = FieldAnalysis.fieldOccurence(files, files, threshold)
            workspace.latest_result = {
                'type': 'field_analysis_occurence',
                'titleCount': titleCount,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None

    
    def country_analysis_year(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            result = CountryAnalysis.country_analysis_by_year(files, start, end, threshold)
            workspace.latest_result = {
                'type': 'country_analysis_year',
                'results': result
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    #透過 WorkspaceService 獲取 workspace（工作區），並提取工作區內的文件並執行學校分析
    def institution_analysis(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            # count, conditionCount, results 
            count, conditionCount, results_institutions, results_publishers = InstitutionAnalysis.analyze(files, start, end, threshold)
            workspace.latest_result = {
                'type': 'institution_analysis',
                'count': count,
                'conditionCount': conditionCount,
                'results_institutions': results_institutions,
                'results_publishers': results_publishers
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def institution_analysis_year(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            result = InstitutionAnalysis.institution_analysis_by_year(files, start, end, threshold)
            workspace.latest_result = {
                'type': 'institution_analysis_year',
                'results': result
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None
    
    def country_analysis_year(self, workspace_id, start, end, threshold):
        workspace = self.repo.get_workspace(workspace_id)
        if workspace:
            files = workspace.files
            count, conditionCount, results = CountryAnalysis.country_analysis_by_year(files, files, start, end, threshold)
            workspace.latest_result = {
                'type': 'country_analysis',
                'count': count,
                'conditionCount': conditionCount,
                'conditionCount': conditionCount,
                'results': results
            }
            self.repo.update_workspace(workspace)
            return workspace.latest_result
        return None 

    