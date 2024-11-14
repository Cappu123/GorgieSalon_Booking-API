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

    """
    Creates a JWT access token with the given user data and expiration time.

    Args:
    - data (dict): The data to include in the token payload (e.g., username, role).

    Returns:
    - str: The generated JWT token as a string.

    Example:
    - create_access_token(data={"user_name": "johndoe", "role": "admin"})
    """

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_access_token(token: dict, credentials_exception):

    """
    Verifies the validity of the JWT token.

    Args:
    - token (dict): The JWT token to verify.
    - credentials_exception (HTTPException): Exception to raise if token validation fails.

    Returns:
    - schemas.TokenData: The decoded token data (username, role).

    Raises:
    - JWTError: If the token is invalid or expired.
    """

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
    

def get_current_user(token: schemas.TokenData = Depends(oauth2_scheme), 
                     db: Session = Depends(database.get_db)):
    
    """
    Retrieves the current authenticated user from the database based on the provided JWT token.

    Args:
    - token (schemas.TokenData): The JWT token passed by OAuth2.
    - db (Session): The database session used to query user data.

    Returns:
    - models.User | models.Admin | models.Stylist: The authenticated user, either an Admin, Stylist, or regular User.

    Raises:
    - HTTPException: If the token is invalid, expired, or if no user is found.
    """

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



def get_current_admin(token: schemas.TokenData = Depends(oauth2_scheme), 
                      db: Session = Depends(database.get_db)):
      
      """
    Retrieves the current authenticated admin from the database based on the provided JWT token.

    Args:
    - token (schemas.TokenData): The JWT token passed by OAuth2.
    - db (Session): The database session used to query admin data.

    Returns:
    - models.Admin: The authenticated admin user.

    Raises:
    - HTTPException: If the token is invalid, expired, or if no admin is found.
    """
      
      credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail=f"Access restricted: Admin privileges required", 
                                          headers={"WWW-Authenticate": "Bearer"})
      
      token = verify_access_token(token, credentials_exception)

      admin = db.query(models.Admin).filter(
        models.Admin.username == token.username, 
        models.Admin.role == token.role).first()
      
      if not admin:
        raise credentials_exception
      return admin



def get_current_stylist(token: schemas.TokenData = Depends(oauth2_scheme), 
                      db: Session = Depends(database.get_db)):
      
      """
    Retrieves the current authenticated stylist from the database based on the provided JWT token.

    Args:
    - token (schemas.TokenData): The JWT token passed by OAuth2.
    - db (Session): The database session used to query stylist data.

    Returns:
    - models.Stylist: The authenticated stylist user.

    Raises:
    - HTTPException: If the token is invalid, expired, or if no stylist is found.
    """
      
      credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                                          detail=f"Access restricted: Only for stylists", 
                                          headers={"WWW-Authenticate": "Bearer"})
      token = verify_access_token(token, credentials_exception)

      stylist = db.query(models.Stylist).filter(
        models.Stylist.username == token.username, 
        models.Stylist.role == token.role).first()
      
      if not stylist:
        raise credentials_exception
      return stylist


