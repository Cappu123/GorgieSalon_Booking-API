from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(
    prefix="/admins",
    tags=['Admins']
)


@router.post("/create_user", status_code=status.HTTP_201_CREATED, response_model=schemas.UserCreateResponse)
def Create_user(user: schemas.UserCreate, db: Session = Depends(get_db), 
                current_user: int = Depends(authorization.get_current_user)):
    """Admin creates a new user"""
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
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Can not perform the requested action, Unauthorized access")

        # Hash the password
        hashed_password = helper_functions.hash_password(user.password)

        # Prepare data to exclude fields not meant to be directly user-controlled (like 'role')
        user_data = user.dict
        user_data["password"] = hashed_password  # Add the hashed password manually

        # Create a new user instance with the filtered data
        new_user = models.User(**user_data)
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
    

@router.delete("/delete_user/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_profile(db: Session = Depends(get_db), 
                        current_user: int = Depends(authorization.get_current_user)):
    """Admin deletes a user's profile"""

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    db.delete(user)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.get("/users", response_model=schemas.UserCreateResponse)
def view_all_users(db: Session = Depends(get_db), 
                     current_user: int = Depends(authorization.get_current_user)):
    """Admins can see all users"""
    user = db.query(models.User).all()
    return user



@router.post("/stylists", status_code=status.HTTP_200_OK, 
             response_model=List[schemas.StylistwithServicesResponse])

def list_stylists(db: Session = Depends(get_db), 
                  current_user: int = Depends(authorization.get_current_user)):
    """Admin can see all stylists(active, suspended, verified, non-verified)"""

    stylist = db.query(models.Stylist).all()
    return stylist



@router.post("/stylists", status_code=status.HTTP_200_OK, 
             response_model=List[schemas.StylistwithServicesResponse])

def list_stylists(db: Session = Depends(get_db), 
                  current_user: int = Depends(authorization.get_current_user)):
    """Admin can see all unverified stylists"""

    stylist = db.query(models.Stylist).filter_by(models.Stylist.verified == False)
    return stylist


@router.post("/stylists/verify/{stylist_id}", status_code=status.HTTP_200_OK)
def approve_stylist(stylist_id: int, db: Session = Depends(get_db), 
                    current_user: int = Depends(authorization.get_current_user)):
    
    """Admins approve a stylist application."""
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    if stylist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Stylist not found.")
    stylist.verified = True
    db.commit()
    return {"message": "Stylist approved successfully."}


@router.post("/stylists/suspend/{stylist_id}", status_code=status.HTTP_200_OK)
def approve_stylist(stylist_id: int, db: Session = Depends(get_db), 
                    current_user: int = Depends(authorization.get_current_user)):
    
    """Admins can suspend stylist's account."""
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    if stylist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Stylist not found.")
    stylist.is_active = False
    db.commit()
    return {"message": "Stylist approved successfully."}


