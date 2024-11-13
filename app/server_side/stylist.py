from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session, selectinload
from typing import List


router = APIRouter(
    prefix="/stylists",
    tags=['Stylists']
)



@router.get("/", response_model=List[schemas.StylistResponse])
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



@router.post("/stylists_filtered", response_model=List[schemas.StylistResponse])
def filter_stylists(stylist_filter: schemas.StylistFilter, 
                    db: Session = Depends(get_db), current_user: schemas.UserValidationSchema = 
                    Depends(authorization.get_current_user)):
    try:
        query = db.query(models.Stylist)#Base query before filtering

        # Apply filters if they are provided
        if stylist_filter.service_id:
            query = query.join(models.Stylist.services).filter(models.Service.service_id == stylist_filter.service_id)


        if stylist_filter.specialization:
            query = query.filter(models.Stylist.specialization.ilike(f"%{stylist_filter.specialization}%"))

        if stylist_filter.rating:
            query = query.filter(models.Stylist.rating >= stylist_filter.rating)

        # Apply pagination
        stylists = query.limit(stylist_filter.limit).offset(stylist_filter.offset).all()
    
        return stylists
    except Exception as e:
        db.rollback()
        print(f"Database error: {e}")

    raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving stylists. Please try again later."
        )


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
    

