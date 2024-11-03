from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/bookings",
    tags=['Bookings']
)


@router.post("/", response_model=schemas.BookingResponse, 
             status_code=status.HTTP_201_CREATED)
def create_service_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db), 
                           current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """Create service booking with a stylist"""
    
    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Service not found"
        )
    
    # Check if the stylist exists
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    if not stylist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Stylist not found"
        )
    
    # Ensure the stylist provides the specified service
    if service not in stylist.services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist does not offer this service"
        )
    
    # Check if the stylist is available at the specified time
    conflicting_booking = db.query(models.Booking).filter(
        models.Booking.stylist_id == booking.stylist_id,
        models.Booking.appointment_time == booking.appointment_time,
        models.Booking.status == "confirmed"  #if stylist has aready confirmed booking status
    ).first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist is already booked at this time"
        )
    
    # Create a new booking
    new_booking = models.Booking(
        user_id=current_user.id,
        service_id=booking.service_id,
        stylist_id=booking.stylist_id,
        appointment_time=booking.appointment_time,
        status="pending"  # Set initial status to "pending" for review by stylist
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return new_booking




@router.post("/{booking_id}", response_model=schemas.BookingResponse)
def accept_booking(booking_id: int, booking: schemas.BookingCreate, 
                           db: Session = Depends(get_db), 
                           current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)):
    """Stylist accepts booking request"""

    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.id == booking.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stylist not found")
    
    # Check if the booking exists
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Booking not found"
        )

    # Ensure that the booking belongs to the current stylist
    if booking.stylist_id != current_stylist.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not authorized to manage this booking"
        )

    # Check if the booking is already confirmed or rejected
    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Booking is already confirmed or rejected"
        )

    # Accept the booking
    booking.status = "confirmed"
    db.commit()
    db.refresh(booking)

    return booking



@router.post("/", response_model=schemas.BookingResponse)
def reject_booking(booking_id: int, db: Session = Depends(get_db), 
                   current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)
):
    # Check if the booking exists
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Booking not found"
        )

    # Ensure that the booking belongs to the current stylist
    if booking.stylist_id != current_stylist.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not authorized to manage this booking"
        )

    # Check if the booking is already confirmed or rejected
    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Booking is already confirmed or rejected"
        )

    # Reject the booking
    booking.status = "rejected"
    db.commit()
    db.refresh(booking)

    return booking



@router.get("/", response_model=List[schemas.BookingResponse])
def get_booking(db: Session = Depends(get_db),
    current_user: schemas.UserValidationSchema = Depends(authorization.get_current_admin)  
):
    bookings = db.query(models.Booking).all()
    if not bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bookings found."
        )
    return bookings