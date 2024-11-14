from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import authorization, database, helper_functions, models, schemas
from fastapi.security.oauth2 import OAuth2PasswordRequestForm



router = APIRouter(tags=['Authentication'])

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(database.get_db)):
    
    """
    Authenticate a user and generate a Bearer token.

    This endpoint allows users (Admins, Stylists, and Clients) to log in to the application by providing
    their username and password. The system will verify the credentials across the following tables:
    - Admins table
    - Stylists table
    - Clients (User) table

    If the credentials are correct, an access token is generated and returned for use in subsequent requests.

    Parameters:
    - user_credentials: The login credentials (username and password) provided by the user.
    - db: The database session dependency for querying the database.

    Returns:
    - A dictionary containing the `access_token` and its `token_type` (bearer).
    
    Raises:
    - HTTPException: If the provided credentials are invalid or no matching user is found.
    """
    
    user = None
    role = None

    # Check in the Admins table
    user = db.query(models.Admin).filter(models.Admin.username == user_credentials.username).first()
    if user:
        if helper_functions.verify_password(user_credentials.password, user.password):
            role = user.role
        else:       
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    # Check in the Stylists table if not found in Admins
    if not user:
        user = db.query(models.Stylist).filter(models.Stylist.username == user_credentials.username).first()
        if user:
            if helper_functions.verify_password(user_credentials.password, user.password):
                role = user.role
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # Check in the Clients table if not found in Admins or Stylists
    if not user:
        user = db.query(models.User).filter(models.User.username == user_credentials.username).first()
        if user:        
            if helper_functions.verify_password(user_credentials.password, user.password):
                role = user.role
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    # If no user was found in any of the tables, raise an authentication error
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create an access token with the user's ID and role
    access_token = authorization.create_access_token(data={"user_name": user.username, "role": role})

    return {"access_token": access_token, "token_type": "bearer"}