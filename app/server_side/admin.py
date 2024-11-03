from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List, Union


router = APIRouter(
    prefix="/admins",
    tags=['Admins']
)


@router.post("/add_services", response_model=schemas.ServiceResponse)
def add_services(service: schemas.ServiceCreate, 
                 db: Session = Depends(get_db), 
                 current_admin:schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    
    #check if service exists already
    existing_service = db.query(models.Service).filter(models.Service.id == service.service_id)
    if existing_service:

        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service with this id already exists"
            )
    new_service = models.Service(**service.dict())
    #ad the new service to the database

    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    return new_service



@router.post("/add_stylists", response_model=schemas.StylistResponse)
def register_stylists(stylist: schemas.StylistCreate, 
                   db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    
    # Check if admin with the same username or email already exists
    existing_stylist = db.query(models.Stylist).filter(
        (models.Stylist.username == stylist.username) | 
        (models.Stylist.email == stylist.email)
    ).first()
    
    if existing_stylist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A stylist with this username or email already exists"
        )
    
    # Create a new stylist instance
    new_stylist = models.Admin(**stylist.dict())

    # You may want to hash the password before saving
    new_stylist.password = helper_functions.hash_password(stylist.password)  

    # Add the new admin to the database
    db.add(new_stylist)
    db.commit()
    db.refresh(new_stylist)

    return schemas.AdminResponse(**new_stylist.__dict__)



@router.post("/create_admin", response_model=schemas.AdminResponse)
def register_admin(admin: schemas.AdminCreate, 
                   db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    
    # Check if admin with the same username or email already exists
    existing_admin = db.query(models.Admin).filter(
        (models.Admin.username == admin.username) | 
        (models.Admin.email == admin.email)
    ).first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this username or email already exists"
        )
    # Create a new admin instance
    new_admin = models.Admin(**admin.dict())

    # hash the password before saving
    new_admin.password = helper_functions.hash_password(admin.password)  

    # Add the new admin to the database
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return schemas.AdminResponse(**new_admin.__dict__)


@router.get("/bookings", response_model=List[schemas.BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)  
):
    
    bookings = db.query(models.Booking).all()
    if not bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bookings found."
        )
    return bookings



@router.get("/users", response_model=schemas.UserResponse)
def view_all_users(db: Session = Depends(get_db), 
                     current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    """Admins can see all users"""

    users = db.query(models.User).all()
    return users



@router.get("/stylists", response_model=List[schemas.StylistResponse])
def view_all_users(db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    """Admins can see all stylists"""

    stylists = db.query(models.Stylist).all()
    return stylists

