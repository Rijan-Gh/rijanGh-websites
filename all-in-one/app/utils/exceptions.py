class BusinessError(Exception):
    """Custom exception for business logic errors"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DatabaseError(Exception):
    """Custom exception for database errors"""
    def __init__(self, message: str, code: str = "DATABASE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class NotFoundError(Exception):
    """Custom exception for not found errors"""
    def __init__(self, message: str, code: str = "NOT_FOUND"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class PaymentError(Exception):
    """Custom exception for payment errors"""
    def __init__(self, message: str, code: str = "PAYMENT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class RateLimitError(Exception):
    """Custom exception for rate limiting"""
    def __init__(self, message: str, code: str = "RATE_LIMIT_EXCEEDED"):
        self.message = message
        self.code = code
        super().__init__(self.message)