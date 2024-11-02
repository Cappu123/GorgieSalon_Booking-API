from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import database, models
from . import schemas
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .configuration import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_access_token(token: dict, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("user_name")
        role: str = payload.get("role")

        if username is None or role is None:
            raise credentials_exception
        
        token_data = schemas.TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
    return token_data
    

def get_current_user(token: schemas.TokenData = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail=f"could not validate credentials", 
                                          headers={"WWW-Authenticate": "Bearer"})

    token = verify_access_token(token, credentials_exception)


    user = db.query(models.Admin).filter(
        models.Admin.username == token.username, 
        models.Admin.role == token.role).first()
    
    if not user:
        user = db.query(models.Stylist).filter(
            models.Stylist.username == token.username, 
            models.Stylist.role == token.role).first()
    if not user:
        user = db.query(models.User).filter(
            models.User.username == token.username, 
            models.User.role == token.role).first()
    if user is None:
        raise credentials_exception
    
    return user



def get_current_admin(db: Session = Depends(database.get_db), 
                      token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token, credentials_exception)
    
    admin = db.query(models.Admin).filter(models.Admin.username == token_data.username).first()
    
    if admin is None:
        raise credentials_exception

    return admin


