from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session, joinedload
from typing import List, Union


router = APIRouter(
    prefix="/admins",
    tags=['Admins']
)


@router.post("/create_services", response_model=List[schemas.ServiceResponse], status_code=status.HTTP_201_CREATED)
def create_services(
    services: List[schemas.ServiceCreate],  
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)
):
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
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stylist with ID {stylist_id} not found")
    
    # Commit the changes to the database
    db.commit()
    db.refresh(service)
    
    return service



@router.delete("/delete_service/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = 
                   Depends(authorization.get_current_admin)):
    
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
        stylist_with_services = db.query(models.Stylist).options(joinedload(models.Stylist.services)).filter(models.Stylist.id == new_stylist.id).first()


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
    """admin verifies booking request"""

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
    """Admin Rejects Booking"""

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
    """Admins can see all users"""

    users = db.query(models.User).all()
    return users



@router.get("/stylists", response_model=List[schemas.StylistResponse])
def view_all_stylists(db: Session = Depends(get_db), 
                   current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)):
    """Admins can see all stylists"""

    stylists = db.query(models.Stylist).all()
    return stylists