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
                 current_user = Depends(authorization.get_current_user)):
    """Retrieves all stylists"""
    stylists = db.query(models.Stylist).all()



@router.get("/stylists/{stylist_id}", response_model=schemas.StylistResponse)
def get_stylist(stylist_id: int, db: Session = Depends(get_db), 
                current_user = Depends(authorization.get_current_user)):
    """Retrieves a specific stylist"""
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()
    return stylist



@router.get("/dashboard/{stylist_id}", 
            status_code=status.HTTP_200_OK)
def stylist_dashboard(stylist_id: int, db: Session = Depends(get_db), 
                      current_user = Depends(authorization.get_current_user)):
    """Retrieves Stylists dashboard"""
    stylist = db.query(models.Stylist).filter(models.Stylist.id == stylist_id).first()

    if stylist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The requested stylist profile does not exist")
    
    if stylist.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Cannot perform the requested action, Unauthorized access")

    return "stylist dashboard"

