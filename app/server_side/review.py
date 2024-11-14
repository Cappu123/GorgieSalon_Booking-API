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

@router.post("/stylist", response_model=schemas.ReviewResponse, 
             status_code=status.HTTP_201_CREATED)

def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), 
                  current_user: schemas.UserValidationSchema = Depends(authorization.get_current_user)):
    
    """
    ## Create Stylist Review

    This endpoint enables authenticated clients to submit a review for a stylist. The review includes a rating (1-5) and optional text. Only clients are allowed to submit reviews.

    ### Parameters
    - **review** (ReviewCreate): The data required to create a review, including `stylist_id`, `rating`, and `review_text`.
    - **db** (Session): The database session dependency.
    - **current_user** (UserValidationSchema): The authenticated user who is submitting the review.

    ### Returns
    - **ReviewResponse**: The newly created review, including the stylist's ID, rating, review text, and timestamp.

    ### Error Responses
    - **403 Forbidden**: If the user is not a client (i.e., unauthorized role).
    - **404 Not Found**: If either the stylist or user does not exist.
    - **400 Bad Request**: If the provided rating is outside the 1-5 range.
    - **500 Internal Server Error**: If an unexpected error occurs during review creation.

    ### Example Usage
    - **Request**: `POST /stylist`
      ```json
      {
          "stylist_id": 1,
          "rating": 5,
          "review_text": "Excellent service, highly recommend!"
      }
      ```
    - **Response**: Newly created review details:
      ```json
      {
          "id": 1,
          "user_id": 123,
          "stylist_id": 1,
          "rating": 5,
          "review_text": "Excellent service, highly recommend!",
          "created_at": "2024-11-14T12:34:56"
      }
      ```

    ### Important Notes
    - Only users with the role of `client` are allowed to submit reviews.
    - Ratings must be between 1 and 5.
    """
    
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
@router.get("/average_rating", status_code=status.HTTP_200_OK, response_model=float
)
def stylist_average_rating(stylist_id: int, db: Session = Depends(get_db), 
                           current_user: schemas.UserValidationSchema = 
                           Depends(authorization.get_current_user)) -> float:

    """
    ## Get Stylist's Average Rating
    
    This endpoint calculates the average rating for a stylist based on the reviews they have received.
    The rating is calculated as an average of all the reviews associated with the stylist. If no reviews are found,
    a rating of 0.0 is returned.

    ### Parameters
    - **stylist_id** (int): The unique identifier for the stylist whose average rating is to be retrieved.
    - **db** (Session): The database session dependency.

    ### Returns
    - **float**: The average rating for the stylist, rounded to two decimal places. If no reviews exist, the rating is 0.0.

    ### Error Responses
    - **500 Internal Server Error**: If there is an issue with calculating the average rating due to a database error.

    ### Example Usage
    - **Request**: `GET /average_rating?stylist_id=1`
    - **Response**:
      ```json
      4.5
      ```

    ### Important Notes
    - The average rating is calculated based on all the reviews associated with the stylist's ID.
    - If no reviews exist for the stylist, the function returns a rating of 0.0.
    """
    try:
        # Calculate the average rating
        average_rating = get_average_rating(stylist_id, db)
        return average_rating
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
