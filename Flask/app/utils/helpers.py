"""Utility Functions"""

def example_helper_function(param):
    """An example helper function."""
    print(f"Helper function called with: {param}")
    return True

# Add other common utility functions here, e.g.,
# - Date/time formatting
# - String manipulation
# - Custom decorators (though some might fit better elsewhere)
# - Functions interacting with external APIs in a generic way

from flask import jsonify # Or directly return dicts if Flask-RESTX handles jsonify

def api_success_response(data, status_code=200):
    """标准成功响应格式化"""
    response = {
        "code": 0,  # 固定为0表示业务成功, per API规范文档.md
        "message": "Success", # 固定为 "Success", per API规范文档.md
        "data": data
    }
    return response, status_code

def api_error_response(message, error_code, status_code=400, errors=None):
    """标准错误响应格式化"""
    response = {
        "code": error_code, # 自定义业务错误码
        "message": message, # 清晰的错误信息
        "data": None # 固定为 null
    }
    if errors: # 可选，提供详细字段错误 (用于表单校验)
        response["errors"] = errors
    return response, status_code

