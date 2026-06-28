from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserOut, UserUpdate
from .. import security

router = APIRouter(prefix="/api/users", tags=["用户管理"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=409, detail="用户名已存在")
    h, s = security.hash_password(data.password)
    user = User(
        username=data.username,
        password_hash=h,
        salt=s,
        display_name=data.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{uid}", response_model=UserOut)
def update_user(uid: int, data: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.password:
        h, s = security.hash_password(data.password)
        user.password_hash, user.salt = h, s
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{uid}")
def delete_user(uid: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    db.delete(user)
    db.commit()
    return {"ok": True}
