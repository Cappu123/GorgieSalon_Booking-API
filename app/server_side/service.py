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
    """Retrieves all services"""
    services = db.query(models.Service).options(joinedload(models.Service.stylists)).all()

    return services


@router.get("/{service_id}", response_model=schemas.ServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_admin: schemas.UserValidationSchema = Depends(authorization.get_current_admin)
):
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
