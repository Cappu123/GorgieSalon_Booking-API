from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/bookings",
    tags=['Bookings']
)



@router.get("/", response_model=List[schemas.BookingResponse])
def get_booking(
    db: Session = Depends(get_db),
    current_user: models.Admin = Depends(authorization.get_current_admin)  
):
    bookings = db.query(models.Booking).all()
    if not bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bookings found."
        )
    return bookings



@router.post("/{service_id}", response_model=schemas.BookingResponse)
def verify_booking_request(service_id: int, booking: schemas.BookingCreate, 
                           db: Session = Depends(get_db), 
                           current_user = Depends(authorization.get_current_user)):

    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stylist not found")
    
    # Create a new booking
    new_booking = models.Booking(
        user_id=current_user.id,
        service_id=booking.service_id,
        stylist_id=booking.stylist_id,
        appointment_time=booking.appointment_time,
        status="pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking

@router.post("/{service_id}", response_model=schemas.BookingResponse)
def create_service_booking(service_id: int, booking: schemas.BookingCreate, 
                           db: Session = Depends(get_db), 
                           current_user = Depends(authorization.get_current_user)):

    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stylist not found")
    
    # Create a new booking
    new_booking = models.Booking(
        user_id=current_user.id,
        service_id=booking.service_id,
        stylist_id=booking.stylist_id,
        appointment_time=booking.appointment_time,
        status="pending"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking
