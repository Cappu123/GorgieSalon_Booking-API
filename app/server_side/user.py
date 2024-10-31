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
             response_model=schemas.UserCreateResponse) 
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
    

@router.get("/profile/{user_id}", response_model=schemas.UserResponseBase)
def get_user_profile(user_id: int, db: Session = Depends(get_db), 
current_user = Depends(authorization.get_current_user)):
    """Users retrieving a specific user's(client) info"""

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"user with id: {user_id} does not exist")
    return user



@router.put("/profile/update/", response_model=schemas.UserResponseBase)
def update_user_profile(updated_profile: schemas.UserCreate, db: Session = Depends(get_db), 
                        current_user: int = Depends(authorization.get_current_user)):
    """Updates a user's profile"""

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    
    for key, value in updated_profile.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    return user



@router.delete("/profile/delete/", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_profile(db: Session = Depends(get_db), 
                        current_user: int = Depends(authorization.get_current_user)):
    """Deletes a user's profile"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    db.delete(user)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.put("/profile/change_password/", response_model=schemas.UserResponseBase)
def update_user_password(password_change: schemas.PasswordChange, db: Session = Depends(get_db), 
                         current_user: int = Depends(authorization.get_current_user)):
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



@router.get("/stylists", response_model=List[schemas.StylistwithServicesResponse])
def list_stylists(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), 
                  current_user: int = Depends(authorization.get_current_user)):
    """Retrieve a list of stylists"""
    stylists = db.query(models.Stylist).offset(skip).limit(limit).all()
    return stylists



@router.get("/stylists/{stylist_id}", response_model=schemas.StylistwithServicesResponse)
def get_stylist_profile(stylist_id: int, db: Session = Depends(get_db), 
                        current_user: int = Depends(authorization.get_current_user)):
    """Retrieve a specific stylist's profile"""
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id, 
                                              models.Stylist.verified == True, 
                                              models.Stylist.is_active == False).first()
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Stylist with id {stylist_id} does not exist")
    return stylist



@router.get("/stylists/search", response_model=List[schemas.StylistCreateResponse])
def search_stylists(query: str, db: Session = Depends(get_db)):
    """Search for stylists by name or specialty"""

    stylists = db.query(models.Stylist).filter(
        (models.Stylist.bio.ilike(f"%{query}%")) |
        (models.Stylist.username.ilike(f"%{query}%")) |
        (models.Stylist.specialization.ilike(f"%{query}%"))
    ).all()
    return stylists



@router.post("/bookings", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db),
                   current_user: int = Depends(authorization.get_current_user)):
    
    """Create a booking for a client"""
    booking_data= booking.dict()
    new_booking = models.Booking(**booking_data)

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking
     