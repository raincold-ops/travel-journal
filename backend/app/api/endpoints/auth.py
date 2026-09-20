"""注册、登录和个人资料接口。"""

from fastapi import APIRouter

from backend.app.api.deps import CurrentUser, Database
from backend.app.core.security import create_access_token
from backend.app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse, UserUpdate
from backend.app.services import auth_service


router = APIRouter(prefix="/auth", tags=["01 · 账号"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Database) -> TokenResponse:
    """创建账号，并直接返回可用于后续请求的登录令牌。"""

    user = auth_service.register_user(db, payload)
    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database) -> TokenResponse:
    """使用用户名或邮箱登录。"""

    user = auth_service.authenticate_user(db, payload.account, payload.password)
    return TokenResponse(access_token=create_access_token(user.id), user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def read_me(current_user: CurrentUser) -> UserResponse:
    """读取当前登录用户资料。"""

    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_me(payload: UserUpdate, db: Database, current_user: CurrentUser) -> UserResponse:
    """修改用户名、头像或个人简介。"""

    return UserResponse.model_validate(auth_service.update_user(db, current_user, payload))

