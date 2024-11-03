from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List


router = APIRouter(
    prefix="/stylists",
    tags=['Stylists']
)



@router.get("/stylists", response_model=List[schemas.StylistResponse])
def get_stylists(db: Session = Depends(get_db), 
                 current_stylist: schemas.UserValidationSchema = 
                 Depends(authorization.get_current_stylist)):
    """Retrieves all stylists"""
    
    # Query all stylists from the database
    try:
        stylists = db.query(models.Stylist).all()

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
                current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)):
    """Retrieves a specific stylist"""
    try:
        stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
        # Check if stylist was found
        if not stylist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"Stylist with ID {stylist_id} not found")
        return stylist
    except Exception:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the stylist")


@router.get("/dashboard/", 
            status_code=status.HTTP_200_OK)
def stylist_dashboard(stylist_id: int, db: Session = Depends(get_db), 
                      current_stylist: schemas.UserValidationSchema = Depends(authorization.get_current_stylist)):
    """Retrieves Stylists dashboard"""

    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()

    if stylist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested stylist profile does not exist")
    
    if stylist.id != current_stylist.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Cannot perform the requested action, Unauthorized access")

    return "stylist dashboard"

