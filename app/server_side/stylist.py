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



@router.get("/stylists", response_model=List[schemas.StylistResponse])
def get_stylists(db: Session = Depends(get_db), 
                 current_stylist: schemas.UserValidationSchema = 
                 Depends(authorization.get_current_user)):
    """Retrieves all stylists"""
    
    
    # Query all stylists from the database
    try:
        stylists = db.query(models.Stylist).options(selectinload(models.Stylist.services)).all()

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



@router.get("/{stylist_id}", response_model=schemas.StylistResponse)
def get_stylist(stylist_id: int, db: Session = Depends(get_db), 
                current_stylist: schemas.UserValidationSchema = 
                Depends(authorization.get_current_user)):
    """Retrieves a specific stylist"""

    stylist = db.query(models.Stylist).options(selectinload(models.Stylist.services)).filter(
        models.Stylist.id == stylist_id).first()
    # Check if stylist was found
    if not stylist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Stylist with ID {stylist_id} not found")
    return stylist

@router.put("/profile/change_password/", response_model=schemas.StylistResponse)
def update_user_password(password_change: schemas.PasswordChange, db: Session = Depends(get_db), 
                         current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)):
    """Updates a user's password"""

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



@router.get("/dashboard/", status_code=status.HTTP_200_OK)
def stylist_dashboard(db: Session = Depends(get_db), 
                      current_stylist: schemas.UserValidationSchema = 
                      Depends(authorization.get_current_stylist)):
    
    """Retrieves Stylists dashboard"""
    
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
    


