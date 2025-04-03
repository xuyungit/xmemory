from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.session_manager import session_manager

security = HTTPBearer()

# 需要认证的API路径前缀列表
AUTH_REQUIRED_PATHS = [
    "/api/v1/memories",  # 记忆相关的API需要认证
]

async def auth_middleware(request: Request, call_next):
    """Middleware to check authentication"""
    # 检查请求路径是否需要认证
    requires_auth = any(request.url.path.startswith(path) for path in AUTH_REQUIRED_PATHS)
    
    # 如果路径不需要认证，直接放行
    if not requires_auth:
        return await call_next(request)
    
    try:
        credentials: HTTPAuthorizationCredentials = await security(request)
        session_id = credentials.credentials
        
        if not session_manager.validate_session(session_id):
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
        return await call_next(request)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        ) 