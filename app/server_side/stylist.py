from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Query
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session, selectinload
from typing import List
from sqlalchemy import func, label

router = APIRouter(
    prefix="/stylists",
    tags=['Stylists']
)



@router.get("/stylists", response_model=List[schemas.StylistResponse], 
            status_code=status.HTTP_200_OK)

def get_stylists(db: Session = Depends(get_db), 
                 current_stylist: schemas.UserValidationSchema = 
                 Depends(authorization.get_current_user)):
    """
    ## Get All Stylists
    
    This endpoint retrieves a list of all stylists available in the system.
    
    - **Authorization**: Requires the user to be authenticated.
    - **Returns**: A list of stylist profiles, including their associated services.

    ### Parameters:
    - **db**: Database session dependency.
    - **current_stylist**: User validation schema that confirms the current user is authenticated.

    ### Response:
    - **200 OK**: Successfully retrieves the list of stylists.
    - **404 Not Found**: Returned if no stylists are found in the database.

    ### Example Usage:
    - **Request**: `GET /stylists`
    - **Response**: 
      ```json
      [
          {
              "id": 1,
              "username": "stylist1",
              "email": "stylist1@example.com",
              "specialization": "Hair Styling",
              "services": [
                  {
                      "service_id": 1,
                      "name": "Haircut",
                      "price": 20.0
                  },
                  ...
              ]
          },
          ...
      ]
      ```
      ### Error Codes:
    - **404 Not Found**: If no stylists are available in the database.
    - **500 Internal Server Error**: If an unexpected error occurs during data retrieval.

    ### Notes:
    - This endpoint uses `selectinload` to optimize loading of related `services` data, avoiding multiple database queries.
    """    
    
    # Query all stylists from the database
    try:
        stylists = db.query(models.Stylist).options( 
            selectinload(models.Stylist.services)).all()

        # Check if any stylists were found
        if not stylists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No stylists found"
                )

        return stylists

    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="No stylists Found")



@router.get("/{stylist_id}", response_model=schemas.StylistResponse, 
            status_code=status.HTTP_201_CREATED)

def get_stylist(stylist_id: int, db: Session = Depends(get_db), 
                current_stylist: schemas.UserValidationSchema = 
                Depends(authorization.get_current_user)):
    
    """
    ## Update Stylist Password

    This endpoint allows an authenticated stylist to change their password. 

    - **Authorization**: Requires the stylist to be logged in and authenticated.
    - **Verification**: The stylist must provide their current password, which is verified before the new password is saved.

    ### Request Body
    - **old_password**: The stylist's current password.
    - **new_password**: The stylist's desired new password.

    ### Authentication and Authorization
    - The stylist must be logged in to access this endpoint.
    - Only the logged-in stylist can change their password.
    - If the `old_password` does not match, a `403 Forbidden` error is returned.

    ### Error Codes:
    - **401 Unauthorized**: Returned if a stylist attempts to change another stylist's password.
    - **403 Forbidden**: Returned if the `old_password` provided does not match the current password.
    - **404 Not Found**: Returned if the stylist is not found.
    - **500 Internal Server Error**: Returned if an error occurs during password update.

    ### Example Usage:
    - **Request**: `PUT /profile/change_password/`
    - **Response**: Returns stylist profile details as confirmation.

    ### Security Notes:
    - The password is hashed before storing in the database.
    """
    stylist = db.query(models.Stylist).options(selectinload(models.Stylist.services)).filter(
        models.Stylist.id == stylist_id).first()
    # Check if stylist was found
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Stylist with ID {stylist_id} not found")
    return stylist


@router.put("/profile/change_password/", response_model=schemas.StylistResponse, 
            status_code=status.HTTP_201_CREATED)

def update_user_password(password_change: schemas.PasswordChange, db: Session = Depends(get_db), 
                         current_stylist: schemas.UserValidationSchema = 
                         Depends(authorization.get_current_stylist)):
    
    """
    ## Update Stylist Password

    This endpoint allows an authenticated stylist to change their password. 

    - **Authorization**: Requires the stylist to be logged in and authenticated.
    - **Verification**: The stylist must provide their current password, which is verified before the new password is saved.

    ### Request Body
    - **old_password**: The stylist's current password.
    - **new_password**: The stylist's desired new password.

    ### Authentication and Authorization
    - The stylist must be logged in to access this endpoint.
    - Only the logged-in stylist can change their password.
    - If the `old_password` does not match, a `403 Forbidden` error is returned.

    ### Error Codes:
    - **401 Unauthorized**: Returned if a stylist attempts to change another stylist's password.
    - **403 Forbidden**: Returned if the `old_password` provided does not match the current password.
    - **404 Not Found**: Returned if the stylist is not found.
    - **500 Internal Server Error**: Returned if an error occurs during password update.

    ### Example Usage:
    - **Request**: `PUT /profile/change_password/`
    - **Response**: Returns stylist profile details as confirmation.

    ### Security Notes:
    - The password is hashed before storing in the database.
    """

    # Find the user in the database
    stylist = db.query(models.Stylist).filter(models.Stylist.id == current_stylist.id).first()

    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found")
        
    if stylist.id != current_stylist.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )

    # Verify old password
    if not helper_functions.verify_password(password_change.old_password, stylist.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Old password is incorrect")

    try:
        # Hash and update the new password
        stylist.password = helper_functions.hash_password(password_change.new_password)
        db.commit()
        return stylist

    except Exception as e:
        db.rollback()  # Roll back any changes if an error occurs
        print("Database_error: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="An error occurred while changing your password. Please try again later.")


@router.get("/stylists/search", response_model=List[schemas.StylistResponse])

def search_stylists_by_specialization(specialization: str, db: Session = Depends(get_db), 
                                      current_stylist: schemas.UserValidationSchema = 
                                      Depends(authorization.get_current_stylist)):
    """
    ## Search Stylists by Specialization

    This endpoint allows users to search for stylists based on their specialization.
    
    - **specialization**: A keyword for filtering stylists by expertise. 
    - Returns a list of stylists whose specialization contains the keyword.
    - Useful for finding stylists with specific skills, like 'haircut', 'colorist', etc.
    
    ### Example Usage:
    - **Request**: `GET /stylists/search?specialization=haircut`
    - **Response**: List of stylist profiles with relevant expertise.
    
    ### Error Codes:
    - **404**: No stylists found with the specified specialization.
    """


    # Query the database for stylists with the specified specialization
    stylists = db.query(models.Stylist).filter(models.Stylist.specialization.ilike(f"%{specialization}%")).all()
    
    if not stylists:
        raise HTTPException(status_code=404, detail="No stylists found with the specified specialization.")
    
    return stylists


@router.get("/dashboard/", status_code=status.HTTP_200_OK)

def stylist_dashboard(db: Session = Depends(get_db), 
                      current_stylist: schemas.UserValidationSchema = 
                      Depends(authorization.get_current_stylist)):
    
    """
    ## Stylist Dashboard

    This endpoint provides access to the dashboard of a specific stylist. 

    - **Authorization**: Requires an authenticated stylist user.
    - **Response**: Returns a message containing the stylist's username.
    
    ### Authentication and Authorization
    - The endpoint checks the identity of the stylist attempting to access the dashboard.
    - Only the stylist whose ID matches the `current_stylist`'s ID is authorized.
    - If unauthorized access is detected, a `401 Unauthorized` error is returned.

    ### Error Codes:
    - **401 Unauthorized**: Returned if a stylist tries to access a dashboard that is not their own.
    - **404 Not Found**: Returned if the stylist's profile does not exist.

    ### Example Usage:
    - **Request**: `GET /dashboard/`
    - **Response**: `{ "Dashboard of": "stylist_username" }`
    """
    
    stylist = db.query(models.Stylist).filter(models.Stylist.id == current_stylist.id).first()

    # Make sure stylists are tying to access their own dashboard
    if stylist.id != current_stylist.id:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized access"
    )

    if stylist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"The requested stylist profile does not exist")
        
    return {
        "Dashboard of": current_stylist.username
    }
    


