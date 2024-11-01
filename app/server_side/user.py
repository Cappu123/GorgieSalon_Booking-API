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
    

@router.get("/profile/{user_id}", response_model=schemas.UserResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db), 
current_user = Depends(authorization.get_current_user)):
    """Users retrieving a specific user's(client) info"""

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"user with id: {user_id} does not exist")
    return user



@router.put("/profile/update/", response_model=schemas.UserResponse)
def update_user_profile(updated_profile: schemas.UserCreate, db: Session = Depends(get_db)):
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
def delete_user_profile(db: Session = Depends(get_db)):
    """Deletes a user's profile"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    db.delete(user)
    db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.put("/profile/change_password/", response_model=schemas.UserResponse)
def update_user_password(password_change: schemas.PasswordChange, db: Session = Depends(get_db)):
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



@router.get("/services", response_model=List[schemas.ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    """Retrieves all services"""
    services = db.query(models.Service).all()
    return services


@router.get("/services/{service_id}", response_model=schemas.ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db)):

    """Retrieves a specific service"""
    service = db.query(models.Service).filter(models.Service.service_id == service_id).first()
    return service


@router.get("/stylists", response_model=List[schemas.StylistResponse])
def get_stylists(db: Session = Depends(get_db)):
    """Retrieves all stylists"""
    stylists = db.query(models.Stylist).all()



@router.get("/stylists/{stylist_id}", response_model=schemas.StylistResponse)
def get_stylist(stylist_id: int, db: Session = Depends(get_db)):
    """Retrieves a specific stylist"""
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    return stylist



@router.post("/bookings/{service_id}", response_model=schemas.BookingResponse)
def create_service_booking(service_id: int, booking: schemas.BookingCreate, db: Session = Depends(get_db)):

    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stylist not found")
    
    # Create a new booking
    new_booking = models.Booking(
        #user_id=current_user.id,
        service_id=booking.service_id,
        stylist_id=booking.stylist_id,
        appointment_time=booking.appointment_time,
        status="pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking



 
                # current_user = Depends(authorization.get_current_user)
     