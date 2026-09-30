from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import User
from src.auth.security import hash_password, verify_password, create_access_token
from src.api.dependencies import get_current_user
from src.api.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Đăng ký tài khoản người dùng mới."""
    existing_user = db.query(User).filter(User.username == request.username.strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tên đăng nhập đã tồn tại trong hệ thống"
        )
    
    hashed_pwd = hash_password(request.password)
    new_user = User(
        username=request.username.strip(),
        password_hash=hashed_pwd,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token({
        "sub": str(new_user.user_id),
        "username": new_user.username,
        "role": new_user.role
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.user_id,
        username=new_user.username,
        role=new_user.role
    )


@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Xác thực đăng nhập tài khoản."""
    user = db.query(User).filter(User.username == request.username.strip()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = create_access_token({
        "sub": str(user.user_id),
        "username": user.username,
        "role": user.role
    })
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        role=user.role
    )


@router.post("/logout")
def logout():
    """Đăng xuất tài khoản (Xóa phiên làm việc phía client)."""
    return {"status": "success", "message": "Đăng xuất thành công"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Lấy thông tin tài khoản đang đăng nhập."""
    return current_user
