from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

router = APIRouter(
    prefix="/bookings",
    tags=['Bookings']
)


@router.post("/create", response_model=schemas.BookingResponse, 
             status_code=status.HTTP_201_CREATED)
def create_service_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db), 
                           current_user: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_user)):
    
    """Create service booking with a stylist"""
    

    # Ensure only users can create a booking using this route
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please Signin as a client to access"
        )

    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.service_id == booking.service_id).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Service with ID {booking.service_id} not found"
        )
    service_name = service.name #save for later use
    
    # Check if the stylist exists
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    if not stylist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The requested stylist is not found"
        )
    stylist_name = stylist.username #save for later use
    
    # Ensure the stylist provides the specified service
    if service not in stylist.services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist does not offer this service"
        )
    #verify appointmnet data is in the future
    if booking.appointment_time <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Appointment time must be in the future")

    # Check if the stylist has conflicting-booing at the specified time
    conflicting_booking = db.query(models.Booking).filter(
        models.Booking.stylist_id == booking.stylist_id,
        models.Booking.appointment_time == booking.appointment_time, 
        models.Booking.status == "confirmed").first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist is already booked at this time"
        )

    new_booking = models.Booking(**booking.dict(), user_id=current_user.id)

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "id": new_booking.id,
        "user_id": new_booking.user_id,
        "stylist_id": new_booking.stylist_id,
        "stylist_name": stylist_name,
        "service_id": new_booking.service_id,
        "service_name": service_name,
        "appointment_time": new_booking.appointment_time,
        "status": new_booking.status,
    }



@router.post("/create/for/targeted_user", response_model=schemas.BookingResponse, 
             status_code=status.HTTP_201_CREATED)
def create_service_booking(booking_for_targeted_user: schemas.BookingCreateForUser, db: Session = Depends(get_db), 
                           current_user: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_user)):
    
    """Create service booking by stylists or admins
    on behalf of a user"""
    
    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.service_id == booking_for_targeted_user.service_id).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Service with ID {booking_for_targeted_user.service_id} not found"
        )
    service_name = service.name
    
    # Check if the stylist exists
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking_for_targeted_user.stylist_id).first()
    if not stylist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The requested stylist is not found"
        )
    stylist_name = stylist.username
    
    # Ensure the stylist provides the specified service
    if service not in stylist.services:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist does not offer this service"
        )
    #verify appointmnet data is in the future
    if booking_for_targeted_user.appointment_time <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Appointment time must be in the future")

    # Check if the stylist has conflicting-booing at the specified time
    conflicting_booking = db.query(models.Booking).filter(
        models.Booking.stylist_id == booking_for_targeted_user.stylist_id,
        models.Booking.appointment_time == booking_for_targeted_user.appointment_time, 
        models.Booking.status == "confirmed").first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist is already booked at this time"
        )

    new_booking = models.Booking(**booking_for_targeted_user.dict())

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "id": new_booking.id,
        "user_id": new_booking.user_id,
        "stylist_id": new_booking.stylist_id,
        "stylist_name": stylist_name,
        "service_id": new_booking.service_id,
        "service_name": service_name,
        "appointment_time": new_booking.appointment_time,
        "status": new_booking.status,
    }



@router.put("/update", response_model=schemas.BookingResponse)
def update_booking(booking_id: int, updated_booking: schemas.BookingUpdate, 
                   db: Session = Depends(get_db), 
                   current_user: schemas.UserValidationSchema = 
                   Depends(authorization.get_current_user)):
    """
    Update a booking by ID.
    """
    # Fetch the booking from the database
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    
    # Check if booking exists
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Ensure only the user who created the booking can update it
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this booking"
        )
    
    # Verify new appointment time is in the future
    if updated_booking.appointment_time <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Appointment time must be in the future")

    # Check if the stylist has a conflicting booking at the new time
    conflicting_booking = db.query(models.Booking).filter(
        models.Booking.stylist_id == booking.stylist_id,
        models.Booking.appointment_time == updated_booking.appointment_time,
        models.Booking.status == "confirmed",
        models.Booking.id != booking.id  # Exclude the current booking
    ).first()
    
    if conflicting_booking:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Stylist is already booked at this time"
        )
    
    # Update booking details
    if booking.status == "completed" or booking.status == "confirmed":
        raise HTTPException(status=status.HTTP_400_BAD_REQUEST, 
                            details = "Booking is already confirmed or completed. Please try to create a new booking")
    
    booking.appointment_time = updated_booking.appointment_time or booking.appointment_time
    booking.status = booking.status

    db.commit()
    db.refresh(booking)

    # Get stylist and service names for response
    stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
    service = db.query(models.Service).filter(models.Service.service_id == booking.service_id).first()

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "stylist_id": booking.stylist_id,
        "stylist_name": stylist.username if stylist else "Unknown Stylist",
        "service_id": booking.service_id,
        "service_name": service.name if service else "Unknown Service",
        "appointment_time": booking.appointment_time,
        "status": booking.status,
    }



@router.post("/accept/", response_model=schemas.BookingResponse)
def accept_booking(booking_id: int, 
                           db: Session = Depends(get_db), 
                           current_stylist: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_stylist)):
    """Stylist accepts booking request"""

    # Retrieve the booking
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
            detail="Unauthorized access"
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

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "stylist_id": booking.stylist_id,
        "stylist_name": booking.stylist.username,
        "service_id": booking.service_id,
        "service_name": booking.service.name,
        "appointment_time": booking.appointment_time,
        "status": booking.status,
    }


@router.post("/reject/{booking_id}", response_model=schemas.BookingResponse)
def reject_booking(booking_id: int, 
                           db: Session = Depends(get_db), 
                           current_stylist: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_stylist)):
    """Stylist rejects booking request"""

    # Retrieve the booking
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
            detail="Unauthorized access"
        )

    # Check if the booking is already confirmed or rejected
    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Booking is already confirmed or rejected"
        )

    # Accept the booking
    booking.status = "rejected"
    db.commit()
    db.refresh(booking)

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "stylist_id": booking.stylist_id,
        "stylist_name": booking.stylist.username,
        "service_id": booking.service_id,
        "service_name": booking.service.name,
        "appointment_time": booking.appointment_time,
        "status": booking.status,
    }


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, db: Session = Depends(get_db), 
                   current_user: schemas.UserValidationSchema = 
                   Depends(authorization.get_current_user)):
    """
    Delete a booking by ID.
    """
    # Fetch the booking from the database
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    
    # Check if booking exists
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Only allow the user who created the booking or an admin to delete it
    if booking.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this booking"
        )
    
    # Delete the booking
    db.delete(booking)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)





@router.post("/complete/{booking_id}", response_model=schemas.BookingResponse)
def complete_booking(booking_id: int, db: Session = Depends(get_db), 
                     current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)):
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
            detail="Not authorized to manage this booking"
        )

    # Check if the booking is already completed
    if booking.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking already completed"
        )
    # Check if the booking is in a valid state to be completed
    if booking.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking must be confirmed before it can be completed"
        )

    # Update the booking status to completed
    booking.status = "completed"
    db.commit()
    db.refresh(booking)

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "stylist_id": booking.stylist_id,
        "stylist_name": booking.stylist.username,  
        "service_id": booking.service_id,
        "service_name": booking.service.name,  
        "appointment_time": booking.appointment_time,
        "status": booking.status,
    }



@router.get("/", response_model=List[schemas.BookingResponse])
def get_bookings(db: Session = Depends(get_db),
                 current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """
    Get all previous and upcoming bookings for the current user.
    """
    # Get the current time in UTC
    current_time = datetime.now(timezone.utc)

    # Define lists to hold previous and upcoming bookings
    previous_bookings = []
    upcoming_bookings = []

    # Check the user's role and fetch bookings accordingly
    if current_user.role == "user":
        previous_bookings = db.query(models.Booking).filter(
            models.Booking.user_id == current_user.id,
            models.Booking.appointment_time < current_time
        ).order_by(models.Booking.appointment_time.desc()).all()
        
        upcoming_bookings = db.query(models.Booking).filter(
            models.Booking.user_id == current_user.id,
            models.Booking.appointment_time >= current_time
        ).order_by(models.Booking.appointment_time.asc()).all()

    elif current_user.role == "stylist":
        previous_bookings = db.query(models.Booking).filter(
            models.Booking.stylist_id == current_user.id,
            models.Booking.appointment_time < current_time
        ).order_by(models.Booking.appointment_time.desc()).all()
        
        upcoming_bookings = db.query(models.Booking).filter(
            models.Booking.stylist_id == current_user.id,
            models.Booking.appointment_time >= current_time
        ).order_by(models.Booking.appointment_time.asc()).all()

    # Helper function to enrich bookings with stylist and service names
    def enrich_booking(booking):
        stylist = db.query(models.Stylist).filter(models.Stylist.id == booking.stylist_id).first()
        service = db.query(models.Service).filter(models.Service.service_id == booking.service_id).first()
        booking.stylist_name = stylist.username if stylist else "Unknown Stylist"
        booking.service_name = service.name if service else "Unknown Service"
        return booking

    # Apply enrichment to all previous and upcoming bookings
    previous_bookings = [enrich_booking(booking) for booking in previous_bookings]
    upcoming_bookings = [enrich_booking(booking) for booking in upcoming_bookings]

    # Combine previous and upcoming bookings into a single response list
    all_bookings = previous_bookings + upcoming_bookings

    return all_bookings


