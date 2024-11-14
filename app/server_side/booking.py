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
    
    """
    ## Create a Service Booking
    
    This endpoint allows a client to create a booking for a service with a stylist. It checks that the user is a client, 
    the service and stylist exist, the stylist offers the service, the appointment time is in the future, and that there are no conflicting bookings.
    
    ### Parameters
    - **booking** (BookingCreate): The booking details including the service, stylist, and appointment time.
    - **db** (Session): The database session dependency.
    - **current_user** (UserValidationSchema): The currently authenticated user.

    ### Returns
    - **BookingResponse**: A response containing the booking details, including the booking ID, user, stylist, service, and appointment time.

    ### Error Responses
    - **403 Forbidden**: If the user is not a client.
    - **404 Not Found**: If the service or stylist does not exist.
    - **400 Bad Request**: If the stylist does not offer the service, the appointment time is in the past, or the stylist is already booked at the specified time.

    ### Example Usage
    - **Request**:
      ```json
      {
        "service_id": 1,
        "stylist_id": 2,
        "appointment_time": "2024-11-20T10:00:00+00:00"
      }
      ```
    - **Response**:
      ```json
      {
        "id": 1,
        "user_id": 1,
        "stylist_id": 2,
        "stylist_name": "Jane Doe",
        "service_id": 1,
        "service_name": "Haircut",
        "appointment_time": "2024-11-20T10:00:00+00:00",
        "status": "confirmed"
      }
      ```

    ### Important Notes
    - Only clients can create bookings. Other roles will receive a **403 Forbidden** error.
    - The appointment time must be in the future.
    - The stylist must offer the service and be available at the specified time.
    """    

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

def create_service_booking(booking_for_targeted_user: schemas.BookingCreateForUser, 
                           db: Session = Depends(get_db), 
                           current_user: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_user)):
    
    """
    ## Create a Service Booking for a Targeted User
    
    This endpoint allows a stylist or an admin to create a service booking for a user. The booking request will be validated to ensure that:
    - The user is authorized to make the booking (stylist or admin).
    - The specified service and stylist exist.
    - The stylist offers the requested service.
    - The appointment time is in the future.
    - The stylist is available at the specified time.
    
    ### Parameters
    - **booking_for_targeted_user** (BookingCreateForUser): The booking details, including service, stylist, and appointment time for the targeted user.
    - **db** (Session): The database session dependency.
    - **current_user** (UserValidationSchema): The currently authenticated user (stylist or admin).

    ### Returns
    - **BookingResponse**: The booking details, including the booking ID, user, stylist, service, and appointment time.

    ### Error Responses
    - **404 Not Found**: If the service or stylist does not exist.
    - **400 Bad Request**: If the stylist does not offer the service, the appointment time is in the past, or the stylist is already booked at the specified time.

    ### Example Usage
    - **Request**:
      ```json
      {
        "service_id": 1,
        "stylist_id": 2,
        "appointment_time": "2024-11-20T10:00:00+00:00",
        "user_id": 3
      }
      ```
    - **Response**:
      ```json
      {
        "id": 1,
        "user_id": 3,
        "stylist_id": 2,
        "stylist_name": "Jane Doe",
        "service_id": 1,
        "service_name": "Haircut",
        "appointment_time": "2024-11-20T10:00:00+00:00",
        "status": "confirmed"
      }
      ```

    ### Important Notes
    - Only stylists and admins can create bookings for users.
    - The appointment time must be in the future.
    - The stylist must be available for the service and at the specified time.
    """
    
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



@router.put("/update", response_model=schemas.BookingResponse, 
            status_code=status.HTTP_201_CREATED)

def update_booking(
    booking_id: int, 
    updated_booking: schemas.BookingUpdate, 
    db: Session = Depends(get_db), 
    current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)
):
    """
    Update a booking by ID.

    This endpoint allows the user to update a booking, with the following checks:
    - The booking must exist.
    - Only the user who created the booking can update it.
    - The appointment time must be in the future.
    - The stylist must not have conflicting bookings at the new time.
    - Bookings that are confirmed or completed cannot be updated.

    ### Parameters
    - **booking_id** (int): The ID of the booking to update.
    - **updated_booking** (BookingUpdate): The updated booking details (appointment time, etc.).

    ### Returns
    - **BookingResponse**: The updated booking details.

    ### Error Responses
    - **404 Not Found**: If the booking does not exist.
    - **403 Forbidden**: If the user is not authorized to update the booking.
    - **400 Bad Request**: If the appointment time is in the past, or if there is a scheduling conflict, or if the booking status is already confirmed or completed.

    ### Example Request:
    ```json
    {
      "appointment_time": "2024-11-25T14:00:00+00:00"
    }
    ```

    ### Example Response:
    ```json
    {
      "id": 1,
      "user_id": 2,
      "stylist_id": 3,
      "stylist_name": "Jane Doe",
      "service_id": 1,
      "service_name": "Haircut",
      "appointment_time": "2024-11-25T14:00:00+00:00",
      "status": "confirmed"
    }
    ```
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Appointment time must be in the future"
        )

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
    
    # Prevent updating confirmed or completed bookings
    if booking.status in ["completed", "confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Booking is already confirmed or completed. Please create a new booking"
        )
    
    # Update booking details (only the appointment time can be updated)
    booking.appointment_time = updated_booking.appointment_time or booking.appointment_time

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


@router.post("/accept/", response_model=schemas.BookingResponse, 
             status_code=status.HTTP_201_CREATED)

def accept_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)
):
    """
    Stylist accepts a booking request.

    This endpoint allows a stylist to accept a booking request. It ensures:
    - The booking exists.
    - The stylist is authorized to accept the booking.
    - The booking is in a "pending" state (i.e., not already confirmed or rejected).

    ### Parameters
    - **booking_id** (int): The ID of the booking to accept.

    ### Returns
    - **BookingResponse**: The updated booking details.

    ### Error Responses
    - **404 Not Found**: If the booking does not exist.
    - **403 Forbidden**: If the stylist is not authorized to accept the booking.
    - **400 Bad Request**: If the booking is already confirmed or rejected.

    ### Example Request:
    ```json
    {
      "booking_id": 123
    }
    ```

    ### Example Response:
    ```json
    {
      "id": 123,
      "user_id": 1,
      "stylist_id": 2,
      "stylist_name": "Jane Doe",
      "service_id": 3,
      "service_name": "Haircut",
      "appointment_time": "2024-11-25T14:00:00+00:00",
      "status": "confirmed"
    }
    ```
    """

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
            detail="Unauthorized access to this booking"
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


@router.post("/reject/{booking_id}", response_model=schemas.BookingResponse, 
             status_code=status.HTTP_201_CREATED)

def reject_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)
):
    """
    Stylist rejects a booking request.

    This endpoint allows a stylist to reject a booking request. It ensures:
    - The booking exists.
    - The stylist is authorized to reject the booking.
    - The booking is in a "pending" state (i.e., not already confirmed or rejected).

    ### Parameters
    - **booking_id** (int): The ID of the booking to reject.

    ### Returns
    - **BookingResponse**: The updated booking details.

    ### Error Responses
    - **404 Not Found**: If the booking does not exist.
    - **403 Forbidden**: If the stylist is not authorized to reject the booking.
    - **400 Bad Request**: If the booking is already confirmed or rejected.

    ### Example Request:
    ```json
    {
      "booking_id": 123
    }
    ```

    ### Example Response:
    ```json
    {
      "id": 123,
      "user_id": 1,
      "stylist_id": 2,
      "stylist_name": "Jane Doe",
      "service_id": 3,
      "service_name": "Haircut",
      "appointment_time": "2024-11-25T14:00:00+00:00",
      "status": "rejected"
    }
    """
    
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
            detail="Unauthorized access to this booking"
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



@router.delete("/delete/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)
):
    """
    Delete a booking by ID.

    This endpoint allows a user to delete a booking. The user must either be the creator of the booking or an admin.

    ### Parameters
    - **booking_id** (int): The ID of the booking to delete.

    ### Returns
    - **204 No Content**: If the booking was successfully deleted.

    ### Error Responses
    - **404 Not Found**: If the booking does not exist.
    - **403 Forbidden**: If the user is not authorized to delete the booking.

    ### Example Request:
    ```json
    {
      "booking_id": 123
    }
    ```

    ### Example Response:
    HTTP status code: `204 No Content`
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
    if booking.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this booking"
        )
    
    # Delete the booking
    db.delete(booking)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)





@router.post("/complete/{booking_id}", response_model=schemas.BookingResponse, 
             status_code=status.HTTP_201_CREATED)

def complete_booking(
    booking_id: int, 
    db: Session = Depends(get_db), 
    current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)
):
    """
    Marks a booking as completed by the assigned stylist.

    Only the stylist who was assigned to the booking can mark it as completed. The booking must be in a confirmed state before it can be completed.

    ### Parameters:
    - **booking_id** (int): The ID of the booking to mark as completed.

    ### Returns:
    - **BookingResponse**: The updated booking details.

    ### Errors:
    - **404 Not Found**: If the booking does not exist.
    - **403 Forbidden**: If the stylist is not authorized to complete the booking.
    - **400 Bad Request**: If the booking is already completed or not in a confirmed state.
    """
    # Retrieve the booking from the database
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()

    # Check if the booking exists
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Ensure that the current stylist is the one assigned to the booking
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

    # Check if the booking is confirmed (valid state to be completed)
    if booking.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking must be confirmed before it can be completed"
        )

    # Update the booking status to 'completed'
    booking.status = "completed"
    db.commit()
    db.refresh(booking)

    # Return the updated booking details
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



@router.get("/", response_model=List[schemas.BookingResponse], 
            status_code=status.HTTP_200_OK)
def get_bookings(
    db: Session = Depends(get_db),
    current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)
):
    """
    Fetch all past and upcoming bookings for the current user.
    
    Depending on the user's role (either 'user' or 'stylist'), it retrieves:
    - For users: their previous and upcoming bookings based on their user ID.
    - For stylists: their previous and upcoming bookings based on their stylist ID.
    
    Both previous and upcoming bookings are filtered by their respective appointment time, and results 
    are sorted accordingly:
    - Past bookings are ordered by appointment time in descending order.
    - Upcoming bookings are ordered by appointment time in ascending order.

    Additionally, each booking is enriched with:
    - The stylist's username.
    - The service's name.

    Parameters:
    - db: The database session dependency.
    - current_user: The current authenticated user (either stylist or regular user).

    Returns:
    - A list of all previous and upcoming bookings enriched with stylist and service information.
    """
    # Get the current time in UTC to compare with booking appointment times
    current_time = datetime.now(timezone.utc)

    # Define the base query with common filters
    base_query = db.query(models.Booking)

    # Fetch previous and upcoming bookings based on user's role
    if current_user.role == "user":
        # For users, filter bookings by user_id
        previous_bookings = base_query.filter(
            models.Booking.user_id == current_user.id,
            models.Booking.appointment_time < current_time
        ).order_by(models.Booking.appointment_time.desc()).all()

        upcoming_bookings = base_query.filter(
            models.Booking.user_id == current_user.id,
            models.Booking.appointment_time >= current_time
        ).order_by(models.Booking.appointment_time.asc()).all()

    elif current_user.role == "stylist":
        # For stylists, filter bookings by stylist_id
        previous_bookings = base_query.filter(
            models.Booking.stylist_id == current_user.id,
            models.Booking.appointment_time < current_time
        ).order_by(models.Booking.appointment_time.desc()).all()

        upcoming_bookings = base_query.filter(
            models.Booking.stylist_id == current_user.id,
            models.Booking.appointment_time >= current_time
        ).order_by(models.Booking.appointment_time.asc()).all()

    def enrich_bookings(bookings):
        """
        Enrich the list of bookings by adding stylist and service names.
        
        Joins the Booking table with the Stylist and Service tables to fetch the required
        information in one query, reducing the number of database calls.

        Parameters:
        - bookings: The list of bookings to be enriched.

        Returns:
        - The list of bookings with enriched stylist and service names.
        """
        # Extract booking ids to query stylist and service names
        booking_ids = [booking.id for booking in bookings]
        
        # Query the stylist and service information in one go
        stylist_service_query = db.query(models.Booking.id, models.Stylist.username, models.Service.name).join(
            models.Stylist, models.Stylist.id == models.Booking.stylist_id
        ).join(
            models.Service, models.Service.service_id == models.Booking.service_id
        ).filter(models.Booking.id.in_(booking_ids)).all()

        # Create a dictionary mapping booking_id -> stylist_name, service_name
        booking_enrichments = {
            booking.id: {
                "stylist_name": stylist_name,
                "service_name": service_name
            }
            for booking, stylist_name, service_name in stylist_service_query
        }

        # Assign enriched information to each booking
        for booking in bookings:
            enrichment = booking_enrichments.get(booking.id, {})
            booking.stylist_name = enrichment.get("stylist_name", "Unknown Stylist")
            booking.service_name = enrichment.get("service_name", "Unknown Service")

        return bookings

    # Apply enrichment to both previous and upcoming bookings
    previous_bookings = enrich_bookings(previous_bookings)
    upcoming_bookings = enrich_bookings(upcoming_bookings)

    # Combine both lists of bookings and return the result
    all_bookings = previous_bookings + upcoming_bookings

    return all_bookings



