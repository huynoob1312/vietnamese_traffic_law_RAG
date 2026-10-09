from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import User
from src.auth.security import decode_access_token

rag_components = {}

def get_rag_components():
    return rag_components

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Hỗ trợ chế độ Guest: Nếu có token hợp lệ trả về User, nếu không có hoặc không hợp lệ trả về None."""
    if not token:
        return None
    
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    return user


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Yêu cầu xác thực tài khoản: Raise 401 nếu thiếu token hoặc token không hợp lệ."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise credentials_exception
    
    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Yêu cầu quyền Quản trị viên (Admin)."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản không có quyền quản trị viên"
        )
    return current_user