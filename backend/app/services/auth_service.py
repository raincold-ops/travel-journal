"""账号注册、登录和资料修改业务。"""

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, verify_password
from backend.app.models import User
from backend.app.schemas.auth import RegisterRequest, UserUpdate


def register_user(db: Session, payload: RegisterRequest) -> User:
    """校验用户名和邮箱是否重复，然后创建账号。"""

    exists = db.scalar(
        select(User).where(or_(User.username == payload.username, User.email == payload.email.lower()))
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名或邮箱已被使用")

    user = User(
        username=payload.username,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, account: str, password: str) -> User:
    """支持使用用户名或邮箱登录，并校验密码。"""

    user = db.scalar(select(User).where(or_(User.username == account, User.email == account.lower())))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码不正确")
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """修改当前用户可编辑的个人资料。"""

    changes = payload.model_dump(exclude_unset=True)
    if "username" in changes:
        exists = db.scalar(select(User).where(User.username == changes["username"], User.id != user.id))
        if exists:
            raise HTTPException(status_code=409, detail="用户名已被使用")
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

