class BusinessException(Exception):
    """自定义业务异常类"""
    def __init__(self, message, status_code=400, error_code=None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.error_code = error_code  # 对应 API规范文档.md 中的业务错误码

class NotFoundException(BusinessException):
    def __init__(self, message="Resource not found", error_code=40401):
        super().__init__(message, status_code=404, error_code=error_code)

class AuthenticationException(BusinessException):
    def __init__(self, message="Authentication failed", error_code=40102):
        super().__init__(message, status_code=401, error_code=error_code)

class AuthorizationException(BusinessException):
    def __init__(self, message="Forbidden", error_code=40301):
        super().__init__(message, status_code=403, error_code=error_code)

class InvalidUsageException(BusinessException):
    def __init__(self, message="Invalid input", error_code=40001, errors=None):
        super().__init__(message, status_code=400, error_code=error_code)
        self.errors = errors # 用于表单校验的详细字段错误 