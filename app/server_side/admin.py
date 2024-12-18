from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from typing import List, Union


router = APIRouter(
    prefix="/admins",
    tags=['Admins']
)


@router.post("/create_services", response_model=List[schemas.ServiceResponse], 
             status_code=status.HTTP_201_CREATED)
def create_services(
    services: List[schemas.ServiceCreate],  
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)
):
    """
    Create new services in the system.

    This endpoint allows an admin to add one or more services to the database. The request must include
    a list of services, each containing the service name, description, duration, and price. The system
    checks if a service with the same name already exists before adding the new service.

    Parameters:
    - services: A list of service details (name, description, duration, price) to be added.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, checked via dependency injection.

    Returns:
    - A list of `ServiceResponse` objects representing the successfully created services.

    Raises:
    - HTTPException: If the user is not an admin, if a service with the same name already exists,
      or if there is an internal server error during the database operation.
    """

    # Check for admin role
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add services"
        )

    created_services = []  # List to store responses for created services

    for service in services:
        # Check if service with the same name already exists
        existing_service = db.query(models.Service).filter(
            models.Service.name == service.name
        ).first()
        
        if existing_service:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A service with the name {service.name} already exists"
            )

        try:
            # Create a new service instance by unpacking the service data
            new_service = models.Service(**service.dict())  

            # Add the new service to the database
            db.add(new_service)
            db.commit()
            db.refresh(new_service)

            # Retrieve associated stylists if needed, or set as empty if there are none
            stylists = [schemas.StylistCreate(**stylist.__dict__) for stylist in new_service.stylists] if new_service.stylists else []

            # Append the newly created service's response to the list
            created_services.append(schemas.ServiceResponse(
                service_id=new_service.service_id,
                name=new_service.name,
                description=new_service.description,
                duration=new_service.duration,
                price=new_service.price,
                created_at=new_service.created_at,
                stylists=stylists  
            ))

        except Exception as e:
            db.rollback()  # Roll back any changes if an error occurs
            print("Database error:", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while adding the service. Please try again later."
            )

    return created_services




@router.put("/update_service", response_model=schemas.ServiceResponse, status_code=status.HTTP_201_CREATED)
def update_service(service_id: int, service_data: schemas.ServiceUpdate, 
                   db: Session = Depends(get_db), current_admin: schemas.UserValidationSchema = 
                   Depends(authorization.get_current_admin)):
    
    """
    Update the details of an existing service.

    This endpoint allows an admin to update the details of a specific service. The service can be 
    updated with new values for its `name`, `description`, `duration`, `price`, and associated `stylists`. 
    If a stylist is provided, their associations to the service will be updated.

    Parameters:
    - service_id: The ID of the service to be updated.
    - service_data: The new service data containing updated information for the service.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, checked via dependency injection.

    Returns:
    - A `ServiceResponse` object representing the updated service, including the `service_id`, `name`, 
      `description`, `duration`, `price`, and the list of associated stylists.

    Raises:
    - HTTPException:
        - If the user is not an admin, a `403 Forbidden` error is raised.
        - If the service is not found, a `404 Not Found` error is raised.
        - If a stylist ID is provided that does not exist, a `404 Not Found` error is raised.
    """

    # Check for admin role
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add services"
        )

    # Fetch the service to be updated
    service = db.query(models.Service).filter(models.Service.service_id == service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    # Update the service fields
    if service_data.name:
        service.name = service_data.name
    if service_data.description:
        service.description = service_data.description
    if service_data.duration:
        service.duration = service_data.duration
    if service_data.price:
        service.price = service_data.price
    
    # Update the stylists association if provided
    if service_data.stylists is not None:
        # Clear the previous associations
        service.stylists = []  # Reset the stylists list before re-assigning

        for stylist_id in service_data.stylists:
            stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
            if stylist:
                service.stylists.append(stylist)  # Add the stylist to the service
            else:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                    detail=f"Stylist with ID {stylist_id} not found")
    
    # Commit the changes to the database
    db.commit()
    db.refresh(service)
    
    return service



@router.delete("/delete_service/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = 
                   Depends(authorization.get_current_admin)):
    
    """
    Delete a service by its ID.

    This endpoint allows an admin to delete a specific service from the system. Before deleting,
    the service's associations with stylists are removed from the relationship table. Afterward,
    the service is deleted from the database.

    Parameters:
    - service_id: The ID of the service to be deleted.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, checked via dependency injection.

    Returns:
    - A confirmation message indicating the service was deleted successfully.

    Raises:
    - HTTPException:
        - If the user is not an admin, a `403 Forbidden` error is raised.
        - If the service is not found, a `404 Not Found` error is raised.
    """
    
    # Check if the current user is an admin
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete services"
        )

    # Check if the service exists
    service_to_delete = db.query(models.Service).filter(models.Service.service_id == service_id).first()
    if not service_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found"
        )
    
    # Remove the service from all associated stylists in the association table
    # Loop through each stylist and remove the service from the relationship
    db.query(models.StylistService).filter(models.StylistService.service_id == 
                                           service_id).delete(synchronize_session=False)
    
    # Commit changes to the stylists' services relationship
    db.commit()

    # Now delete the service itself
    db.delete(service_to_delete)
    db.commit()

    return {"detail": "Service deleted successfully"}



@router.post("/create_stylist", response_model=List[schemas.StylistResponse])
def create_stylist(
    stylists_data: List[schemas.StylistCreate],  
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)
):
    
    """
    Create one or more stylists and associate them with services.

    This endpoint allows an admin to create new stylist accounts, hash their passwords, and associate them with services. The newly created stylist data, including their associated services, is returned in the response.

    Parameters:
    - stylists_data: A list of stylist data to be created. Each stylist includes username, email, password, bio, and specialization.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, checked via dependency injection.

    Returns:
    - A list of stylist response data, including associated services, for each stylist created.

    Raises:
    - HTTPException:
        - If the user is not an admin, a `403 Forbidden` error is raised.
    """

    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add stylists"
        )

    created_stylists = []

    for stylist_data in stylists_data:
        # Hash the password
        hashed_password = helper_functions.hash_password(stylist_data.password)

        # Create new stylist instance 
        new_stylist = models.Stylist(
            username=stylist_data.username,
            email=stylist_data.email,
            password=hashed_password,
            bio=stylist_data.bio,
            specialization=stylist_data.specialization,
       
        )
        print (new_stylist)

        # Add to database
        db.add(new_stylist)
        db.commit()
        db.refresh(new_stylist)
        

        # Fetch the stylist with their associated services 
        stylist_with_services = db.query(models.Stylist).options(joinedload(models.Stylist.services)).filter(
            models.Stylist.id == new_stylist.id).first()


        # Append created stylist to response list
        created_stylists.append(schemas.StylistResponse.from_orm(stylist_with_services))

    return created_stylists



@router.put("/update_stylist/", response_model=schemas.StylistResponse)
def update_stylist(
    stylist_id: int,
    stylist_data: schemas.StylistUpdate,
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)
):
    
    """
    Update the details of an existing stylist.

    This endpoint allows an admin to update a stylist's information, including their username, email, bio, specialization, and associated services. Only admins are authorized to update stylist details.

    Parameters:
    - stylist_id: The ID of the stylist to be updated.
    - stylist_data: The new stylist data to update, including optional fields such as username, email, bio, specialization, and associated services.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, checked via dependency injection.

    Returns:
    - The updated stylist information, including their associated services.

    Raises:
    - HTTPException:
        - If the user is not an admin, a `403 Forbidden` error is raised.
        - If the stylist with the provided `stylist_id` is not found, a `404 Not Found` error is raised.
        - If any service ID in the `service_ids` list is not found, a `404 Not Found` error is raised.
    """
    
    # Check if the current user is an admin
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update stylists"
        )
    
    # Find the stylist to update
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    if not stylist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stylist with ID {stylist_id} not found"
        )

    # Update stylist fields if provided
    if stylist_data.username is not None:
        stylist.username = stylist_data.username
    if stylist_data.email is not None:
        stylist.email = stylist_data.email
    if stylist_data.bio is not None:
        stylist.bio = stylist_data.bio
    if stylist_data.specialization is not None:
        stylist.specialization = stylist_data.specialization

    # Update the service associations if provided
    if stylist_data.service_ids is not None:
        stylist.services = []  # Reset the current services list before re-assigning
        for service_id in stylist_data.service_ids:
            service = db.query(models.Service).filter(models.Service.service_id == service_id).first()
            if service:
                stylist.services.append(service)  # Add the service to the stylist
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Service with ID {service_id} not found"
                )

    # Commit all changes to the database
    db.commit()
    db.refresh(stylist)  # Refresh the stylist instance to reflect changes

    return stylist



@router.delete("/delete_stylist/", status_code=status.HTTP_204_NO_CONTENT)
def delete_stylist(
    stylist_id: int,
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)
):
    
    """
    Delete a stylist from the system.

    This endpoint allows an admin to delete a stylist from the system. The stylist's associated services are also removed from the relationship table. Only admins are authorized to delete stylists.

    Parameters:
    - stylist_id: The ID of the stylist to be deleted.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, checked via dependency injection.

    Returns:
    - A success message indicating that the stylist has been successfully deleted.

    Raises:
    - HTTPException:
        - If the user is not an admin, a `403 Forbidden` error is raised.
        - If the stylist with the provided `stylist_id` is not found, a `404 Not Found` error is raised.
    """

    # Check if the current user is an admin
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete stylists"
        )

    # Find the stylist to delete
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    if not stylist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stylist with ID {stylist_id} not found"
        )

    # Clear the stylist's associated services
    stylist.services = []  # clearing the associations in the relationship table

    # Delete the stylist from the database
    db.delete(stylist)
    db.commit()

    # Return no content to indicate successful deletion
    return {"detail": "Stylist successfully deleted"}



@router.post("/create_admin", response_model=schemas.AdminResponse)
def register_admin(admin: schemas.AdminCreate, 
                   db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    
    """
    Register a new admin user.

    This endpoint allows an existing admin to register a new admin user. The provided username and email are checked to ensure that no other admin with the same username or email exists. Passwords are hashed before being saved. Only admins are authorized to add new admin users.

    Parameters:
    - admin: The data for the new admin user, including username, email, and password.
    - db: The database session for querying and interacting with the database.
    - current_admin: The currently authenticated admin user, validated via dependency injection to ensure that the current user is an admin.

    Returns:
    - The newly created admin user, including their username, email, and other details.

    Raises:
    - HTTPException:
        - If the current user is not an admin, a `403 Forbidden` error is raised.
        - If an admin with the same username or email already exists, a `400 Bad Request` error is raised.
    """
    
    # Check for admin role
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add stylists"
        )
    # Check if admin with the same username or email already exists
    existing_admin = db.query(models.Admin).filter(
        (models.Admin.username == admin.username) | 
        (models.Admin.email == admin.email)).first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin with this username or email already exists"
        )
    
    # hash the password before saving
    admin.password = helper_functions.hash_password(admin.password)  
    
    # Create a new admin instance
    new_admin = models.Admin(**admin.dict())

    
    # Add the new admin to the database
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin
    


@router.delete("/delete_admin/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(admin_id: int, 
                 db: Session = Depends(get_db), 
                 current_admin: schemas.UserValidationSchema = 
                 Depends(authorization.get_current_admin)):
    
    """
    Delete an admin user.

    This endpoint allows an existing admin to delete another admin user. It performs several checks:
    - Ensures that only admins can delete other admins.
    - Prevents an admin from deleting their own account.
    - Verifies that the specified admin exists before deletion.

    Parameters:
    - admin_id: The ID of the admin to be deleted.
    - db: The database session used to interact with the database.
    - current_admin: The currently authenticated admin user, validated through dependency injection to ensure the current user is an admin.

    Returns:
    - A success message indicating the admin was successfully deleted.

    Raises:
    - HTTPException:
        - If the current user is not an admin, a `403 Forbidden` error is raised.
        - If the current user attempts to delete their own admin account, a `400 Bad Request` error is raised.
        - If the specified admin does not exist, a `404 Not Found` error is raised.
    """
    
    # Check for admin role
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete other admins"
        )

    # Prevent self-deletion
    if current_admin.id == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own admin account"
        )

    # Query for the admin to delete
    admin_to_delete = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    
    # Check if the admin exists
    if not admin_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    # Delete the admin
    db.delete(admin_to_delete)
    db.commit()
    
    return {"message": "Admin successfully deleted"}



@router.post("/accept/{booking_id}", response_model=schemas.BookingResponse)
def accept_booking(booking_id: int,  stylist_id: int,
                           db: Session = Depends(get_db), 
                           current_user: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_admin)):
    
    """
    Admin verifies and accepts a booking request.

    This endpoint allows an authenticated admin to verify and accept a booking request. It performs multiple checks:
    - Ensures the service associated with the booking exists.
    - Verifies the stylist exists.
    - Checks that the current user is an admin.
    - Verifies the booking exists and is still in a "pending" state.
    - Updates the booking status to "confirmed" once accepted.

    Parameters:
    - booking_id: The ID of the booking to accept.
    - stylist_id: The ID of the stylist to be associated with the booking.
    - db: The database session used for querying and committing changes.
    - current_user: The currently authenticated user, validated to be an admin.

    Returns:
    - The updated booking information with the status changed to "confirmed".

    Raises:
    - HTTPException:
        - If the service or stylist does not exist, a `404 Not Found` error is raised.
        - If the current user is not an admin, a `403 Forbidden` error is raised.
        - If the booking does not exist or is not in a "pending" state, a `404 Not Found` or `400 Bad Request` error is raised.
    """

    # Check if the service exists
    service = db.query(models.Service).filter(models.Service.service_id == booking_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stylist not found")
    

    # Ensure the admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage this booking"
        )

    # Check if the booking exists
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Booking not found"
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


@router.post("/reject/", response_model=schemas.BookingResponse)
def reject_booking(booking_id: int, db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    
    """
    Admin rejects a booking request.

    This endpoint allows an authenticated admin to reject a booking request. It performs several checks:
    - Ensures the booking exists.
    - Verifies the current user is an admin.
    - Checks that the booking is still in the "pending" state (not confirmed or rejected).
    - Updates the booking status to "rejected" upon rejection.

    Parameters:
    - booking_id: The ID of the booking to reject.
    - db: The database session used for querying and committing changes.
    - current_admin: The currently authenticated user, validated to be an admin.

    Returns:
    - The updated booking information with the status changed to "rejected".

    Raises:
    - HTTPException:
        - If the booking does not exist, a `404 Not Found` error is raised.
        - If the current user is not an admin, a `403 Forbidden` error is raised.
        - If the booking is not in a "pending" state, a `400 Bad Request` error is raised.
    """

    # Check if the booking exists
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Booking not found"
        )
    
    # Ensure the admin role
    if current_admin.role != "admin":
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




@router.post("/complete/{booking_id}", response_model=schemas.BookingResponse)
def complete_booking(booking_id: int, db: Session = Depends(get_db), 
                     current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    
    """
    Admin marks a booking as completed.

    This endpoint allows an authenticated admin to mark a booking as completed. It performs several checks:
    - Ensures the booking exists.
    - Verifies the current user is an admin.
    - Ensures the booking is in the "confirmed" state before allowing it to be marked as completed.
    - Updates the booking status to "completed" once the checks pass.

    Parameters:
    - booking_id: The ID of the booking to complete.
    - db: The database session used for querying and committing changes.
    - current_admin: The currently authenticated user, validated to be an admin.

    Returns:
    - The updated booking information with the status changed to "completed".

    Raises:
    - HTTPException:
        - If the booking does not exist, a `404 Not Found` error is raised.
        - If the current user is not an admin, a `403 Forbidden` error is raised.
        - If the booking is not in a "confirmed" state, a `400 Bad Request` error is raised.
    """

    # Check if the booking exists
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Ensure the admin role
    if current_admin.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage this booking"
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

    return booking



@router.get("/bookings", response_model=List[schemas.BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)  
):
    """
    Retrieve all bookings in the system.

    This endpoint allows an authenticated admin to retrieve a list of all bookings in the system. 
    It performs the following steps:
    - Ensures the current user is an admin.
    - Retrieves all bookings from the database.
    - If no bookings are found, it raises a `404 Not Found` error.

    Parameters:
    - db: The database session used for querying the bookings.
    - current_admin: The currently authenticated admin user, validated via dependency injection.

    Returns:
    - A list of all bookings in the system.

    Raises:
    - HTTPException:
        - If no bookings are found, a `404 Not Found` error is raised.
    """
    
    bookings = db.query(models.Booking).all()
    if not bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No bookings found."
        )
    return bookings



@router.get("/users", response_model=List[schemas.UserResponse])
def view_all_users(db: Session = Depends(get_db), 
                     current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    
    """
    Retrieve all users in the system.

    This endpoint allows an authenticated admin to retrieve a list of all users (including both stylists and non-stylists) in the system. 
    It performs the following steps:
    - Ensures the current user is an admin.
    - Retrieves all users from the database.

    Parameters:
    - db: The database session used for querying the users.
    - current_admin: The currently authenticated admin user, validated via dependency injection.

    Returns:
    - A list of all users in the system.

    """

    users = db.query(models.User).all()
    return users



@router.get("/stylists", response_model=List[schemas.StylistResponse])
def view_all_stylists(db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    
    """
    Retrieve all stylists in the system.

    This endpoint allows an authenticated admin to retrieve a list of all stylists in the system. 
    It performs the following steps:
    - Ensures the current user is an admin.
    - Retrieves all stylists from the database.

    Parameters:
    - db: The database session used for querying the stylists.
    - current_admin: The currently authenticated admin user, validated via dependency injection.

    Returns:
    - A list of all stylists in the system.

    """

    stylists = db.query(models.Stylist).all()
    return stylists