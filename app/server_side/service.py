from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.orm import joinedload

router = APIRouter(
    prefix="/services",
    tags=['Services']
)

@router.get("/", response_model=List[schemas.ServiceResponse])
def get_services(db: Session = Depends(get_db)):
    
    """
    ## Get All Services
    
    This endpoint retrieves a list of all available services, including their details like name, 
    description, duration, price, creation date, and the associated stylists (if available).

    ### Parameters
    - **db** (Session): The database session dependency.

    ### Returns
    - **List[ServiceResponse]**: A list of service details, where each service includes:
      - `service_id`: The unique identifier of the service.
      - `name`: The name of the service.
      - `description`: A description of the service.
      - `duration`: The duration of the service.
      - `price`: The price of the service.
      - `created_at`: The timestamp when the service was created.
      - `stylists`: A list of stylists associated with the service.

    ### Error Responses
    - **404 Not Found**: If no services are found in the database.
    """

    services = db.query(models.Service).options(joinedload(models.Service.stylists)).all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No service found"
        )
    return services



@router.get("/{service_id}", response_model=schemas.ServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db)):

    """
    ## Get Service Details
    
    This endpoint retrieves the details of a service, including the service's name, description,
    duration, price, creation date, and the list of associated stylists (if available).

    ### Parameters
    - **service_id** (int): The unique identifier for the service whose details are to be retrieved.
    - **db** (Session): The database session dependency.

    ### Returns
    - **ServiceResponse**: A response model containing the service details, including:
      - `service_id`: The unique identifier of the service.
      - `name`: The name of the service.
      - `description`: A description of the service.
      - `duration`: The duration of the service.
      - `price`: The price of the service.
      - `created_at`: The timestamp when the service was created.
      - `stylists`: A list of stylists associated with the service.

    ### Error Responses
    - **404 Not Found**: If the service with the specified ID does not exist.
    
    ### Example Usage
    - **Request**: `GET /services/{service_id}`
    - **Response**:
      ```json
      {
        "service_id": 1,
        "name": "Haircut",
        "description": "A professional haircut service",
        "duration": 30,
        "price": 15.99,
        "created_at": "2024-11-15T12:00:00",
        "stylists": [
          {
            "stylist_id": 1,
            "name": "John Doe",
            "experience": "5 years"
          }
        ]
      }
      ```

    ### Important Notes
    - If the service has no associated stylists, the `stylists` field will be an empty list.
    """
    # Check if the service exists in the database
    service = db.query(models.Service).filter(models.Service.service_id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with id {service_id} not found"
        )

    # Retrieve associated stylists if needed
    stylists = [schemas.StylistCreate(**stylist.__dict__) for stylist in service.stylists] if service.stylists else []

    # Return the service details with stylists
    return schemas.ServiceResponse(
        service_id=service.service_id,
        name=service.name,
        description=service.description,
        duration=service.duration,
        price=service.price,
        created_at=service.created_at,
        stylists=stylists
    )
