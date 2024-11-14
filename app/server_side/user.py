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

    """
    ## User Signup

    This endpoint allows for the creation of a new user account with a unique username and email.
    Upon successful signup, the user's information is stored in the database with a securely hashed password.

    ### Parameters
    - **user** (UserCreate): The user details required to create an account, including `username`, `email`, and `password`.
    - **db** (Session): Database session dependency injection.

    ### Returns
    - **201 Created**: Returns the created user's information, excluding sensitive data like the raw password.
    - **UserResponse**: The response model that defines the returned fields of the user object.

    ### Error Handling
    - **400 Bad Request**: Returned if the username or email already exists in the system.
    - **500 Internal Server Error**: Returned if any other error occurs during the user creation process.

    ### Example Usage
    - **Request**: `POST /users/signup`
    - **Body**: JSON object with `username`, `email`, and `password`
    - **Response**: User object without sensitive fields.

    ### Security Notes
    - Passwords are securely hashed before storage to ensure user data protection.
    """
            
    # Check if a user with the same username or email already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    try:
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
    

@router.get("/profile/", response_model=schemas.UserResponse, 
            status_code=status.HTTP_200_OK
)
def get_user_profile(db: Session = Depends(get_db), 
                     current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    """
    ## Get Current User Profile

    This endpoint retrieves the profile information of the authenticated user.

    ### Parameters
    - **db** (Session): The database session dependency.
    - **current_user** (UserValidationSchema): The authenticated user injected as a dependency.

    ### Returns
    - **200 OK**: Returns the user's profile details as defined in `UserResponse`.
    - **Response Model**: The response model includes fields such as:
      - `username`: The user's unique username.
      - `email`: The user's email address.
      - Other non-sensitive profile information.

    ### Errors
    - **404 Not Found**: Returned if the user profile is not found in the database.
    - **401 Unauthorized**: Raised if an unauthorized attempt is made to access another user's profile.

    ### Usage Example
    - **Request**: `GET /users/profile/`
    - **Response**: JSON object with the user's profile information.
    """

    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"user does not exist")
        
    if user.id != current_user.id:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized access"
    )

    return user
    
       



@router.put("/profile/update/", response_model=schemas.UserResponse)
def update_user_profile(updated_profile: schemas.UserUpdate, 
                        db: Session = Depends(get_db), 
                        current_user: schemas.UserValidationSchema = 
                        Depends(authorization.get_current_user)):
    """Updates a user's profile"""

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
        
    if user.id != current_user.id:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized access"
    )

    for key, value in updated_profile.dict().items():
        setattr(user, key, value)
    try:
        db.commit()
        return user
    except Exception as e:
        db.rollback()  # Roll back any changes if an error occurs
        print("Database error:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating your profile. Please try again later."
        )



@router.delete("/profile/delete/", status_code=status.HTTP_204_NO_CONTENT 
)
def delete_user_profile(db: Session = Depends(get_db), 
                        current_user:schemas.UserValidationSchema = 
                        Depends(authorization.get_current_user)):
    
    """
    ## Delete User Profile

    This endpoint permanently deletes the authenticated user's profile.

    ### Parameters
    - **db** (Session): The database session dependency.
    - **current_user** (UserValidationSchema): The authenticated user who is performing the delete action.

    ### Returns
    - **204 No Content**: Indicates successful deletion of the user's profile.
    
    ### Error Responses
    - **404 Not Found**: Returned if the user's profile does not exist.
    - **401 Unauthorized**: Raised if an unauthorized attempt is made to delete another user's profile.
    - **500 Internal Server Error**: Returned if there is an error during the deletion process.

    ### Example Usage
    - **Request**: `DELETE /users/profile/delete/`
    - **Response**: No content (204 status), confirming the deletion.

    ### Important Notes
    This action is permanent. Ensure that the user is authenticated and aware that deletion is irreversible.
    """

    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested user profile does not exist")
    if user.id != current_user.id:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized access"
    )
    try:
        db.delete(user)
        db.commit()
    
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        db.rollback()  # Roll back any changes if an error occurs
        print("Database_error: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="An error occurred while updating your profile. Please try again later.")



@router.put("/profile/change_password/", response_model=schemas.UserResponse, 
            status_code=status.HTTP_201_CREATED)


def update_user_password(password_change: schemas.PasswordChange, db: Session = Depends(get_db), 
                         current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    
    """
    ## Change User Password

    This endpoint updates the password for the authenticated user.

    ### Parameters
    - **password_change** (PasswordChange): Contains both the `old_password` and `new_password` fields.
    - **db** (Session): The database session dependency.
    - **current_user** (UserValidationSchema): The authenticated user who is attempting to change their password.

    ### Returns
    - **UserResponse**: The updated user profile, confirming that the password was successfully changed.

    ### Error Responses
    - **404 Not Found**: If the user is not found in the database.
    - **401 Unauthorized**: If the authenticated user attempts to change another user's password.
    - **403 Forbidden**: If the provided `old_password` is incorrect.
    - **500 Internal Server Error**: For unexpected errors during the password update.

    ### Example Usage
    - **Request**: `PUT /users/profile/change_password/`
      ```json
      {
          "old_password": "currentpassword123",
          "new_password": "newsecurepassword456"
      }
      ```
    - **Response**: User profile data (without the password).

    ### Important Notes
    - Users must provide their current password to proceed with the password change.
    - This route is only accessible by the authenticated user making the request.
    - Proper error handling ensures sensitive information is protected during validation.
    """

    # Find the user in the database
    user = db.query(models.User).filter(models.User.id == current_user.id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="User not found")
        
    if user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access"
        )

    # Verify old password
    if not helper_functions.verify_password(password_change.old_password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Old password is incorrect")

    try:
        # Hash and update the new password
        user.password = helper_functions.hash_password(password_change.new_password)
        db.commit()
        return user

    except Exception as e:
        db.rollback()  # Roll back any changes if an error occurs
        print("Database_error: ", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail="An error occurred while changing your password. Please try again later.")




    




 
                
     