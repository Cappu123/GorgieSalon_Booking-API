from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.post("/signup", status_code=status.HTTP_201_CREATED, 
             response_model=schemas.UserResponse) 
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Creates a new user"""
    try:
        # Check if a user with the same username or email already exists
        existing_user = db.query(models.User).filter(
            (models.User.username == user.username) | (models.User.email == user.email)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username or email already exists"
            )

        # Hash the password
        hashed_password = helper_functions.hash_password(user.password)
        user.password = hashed_password

        # Create a new user instance with the filtered data
        new_user = models.User(**user.dict())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception as e:
        # Log the exception if using logging for better debugging
        print(f"An error occurred during signup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user. Please try again later."
        )
    

@router.get("/profile/", response_model=schemas.UserResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db), 
                     current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """Users retrieving a specific user's(client) info"""

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"user with id: {user_id} does not exist")
    return user



@router.put("/profile/update/", response_model=schemas.UserResponse)
def update_user_profile(updated_profile: schemas.UserCreate, 
                        db: Session = Depends(get_db), 
                        current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """Updates a user's profile"""

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    
    for key, value in updated_profile.dict().items():
        setattr(user, key, value)

    db.commit()
    return user



@router.delete("/profile/delete/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_profile(db: Session = Depends(get_db), 
                        current_user:schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """Deletes a user's profile"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    db.delete(user)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.put("/profile/change_password/", response_model=schemas.UserResponse)
def update_user_password(password_change: schemas.PasswordChange, db: Session = Depends(get_db), 
                         current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """Updates a user's password"""

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found")
    
    # Verify old password
    if not helper_functions.verify_password(password_change.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Old password is incorrect")
    
    # Hash and update the new password
    user.password = helper_functions.hash_password(password_change.new_password)
    db.commit()
    return user


    
    




 
                
     