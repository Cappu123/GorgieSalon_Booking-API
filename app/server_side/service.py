from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..import schemas, models, helper_functions, authorization
from ..database import get_db
from sqlalchemy.orm import Session
from typing import List

router = APIRouter(
    prefix="/services",
    tags=['Services']
)

@router.get("/services", response_model=List[schemas.ServiceResponse])
def get_services(db: Session = Depends(get_db), 
                 current_user = Depends(authorization.get_current_user)):
    """Retrieves all services"""
    services = db.query(models.Service).all()
    return services


@router.get("/services/{service_id}", response_model=schemas.ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db), 
                current_user = Depends(authorization.get_current_user)):

    """Retrieves a specific service"""
    service = db.query(models.Service).filter(models.Service.service_id == service_id).first()
    return service
