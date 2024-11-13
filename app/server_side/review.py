from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import func

router = APIRouter(
    prefix="/reviews",
    tags=['Reviews']
)

@router.post("/stylist", response_model=schemas.ReviewResponse)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), 
                  current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    
    if current_user.role != "client":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access, Please login as a user to review stylists."
        )
    
    # Check if the stylist exists
    stylist = db.query(models.Stylist).filter(models.Stylist.id == review.stylist_id).first()
    if not stylist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stylist not found"
        )

    # Check if the user exists
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if the rating is between 1 and 5 (already validated in Pydantic schema, but double-checking here)
    if review.rating < 1 or review.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    # Create the new review
    new_review = models.Review(
        user_id=current_user.id,
        stylist_id=review.stylist_id,
        rating=review.rating,
        review_text=review.review_text,
        created_at=datetime.utcnow()
    )
    
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    return new_review



# Function to calculate the average rating for a specific stylist
def get_average_rating(stylist_id: int, db: Session) -> float:
    avg_rating = db.query(func.avg(models.Review.rating)).filter(models.Review.stylist_id == stylist_id).scalar()
    return round(avg_rating, 2) if avg_rating is not None else 0.0


# Route to retrieve average rating of a specific stylist by ID
@router.get("/average_rating")
def stylist_average_rating(stylist_id: int, db: Session = Depends(get_db)) -> float:
    try:
        # Calculate the average rating
        average_rating = get_average_rating(stylist_id, db)
        return average_rating
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
