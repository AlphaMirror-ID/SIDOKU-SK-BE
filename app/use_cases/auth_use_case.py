from sqlalchemy.orm import Session
from app.domain.entities import User
from app.domain.schemas import UserLogin, Token
from app.infrastructure.security import verify_password, create_access_token

def authenticate_user(db: Session, login_data: UserLogin) -> User:
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        return None
    if not verify_password(login_data.password, user.password_hash):
        return None
    return user

def login_for_access_token(db: Session, login_data: UserLogin) -> Token:
    user = authenticate_user(db, login_data)
    if not user:
        return None
    
    access_token = create_access_token(subject=user.username)
    return Token(access_token=access_token, token_type="bearer")