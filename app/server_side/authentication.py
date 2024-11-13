from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import authorization, database, helper_functions, models, schemas
from fastapi.security.oauth2 import OAuth2PasswordRequestForm



router = APIRouter(tags=['Authentication'])

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), 
          db: Session = Depends(database.get_db)):
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