from pydantic import BaseModel, EmailStr, validator, condecimal
from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal, Optional

#################################################

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime
    

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: EmailStr
    username: str

    class Config:
        from_attributes = True

class UserUpdateResponse(UserResponse):
    message: str
###############################################


class TokenData(BaseModel):
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

    class Config:
        from_attributes = True


######################################################


class ServiceCreate(BaseModel):
    name: str
    description: str
    duration: float
    price: float


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    stylists: Optional[List[int]] = None  # List of stylist IDs to update the relationship

    class Config:
        from_attributes = True

class StylistCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    bio: str
    specialization: str

    #service_ids: Optional[List[int]] = []
 
    class Config:
        from_attributes = True


#######################################################


class ServiceResponse(BaseModel):
    service_id: int
    name: str
    description: str
    duration: int
    price: float
    created_at: datetime
    #stylists: Optional[List[int]] = []



class StylistResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    bio: str
    specialization: str
    active: bool
    services: List[ServiceResponse]  # This represents the related services for each stylist

    class Config:
        from_attributes = True


    

    class Config:
        from_attributes = True



class StylistProfileUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    bio: Optional[str]
    specialization: Optional[str]

    class Config:
        from_attributes = True


class StylistUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    bio: Optional[str]
    specialization: Optional[str]
    service_ids: Optional[List[int]]  # List of service IDs to update associations

    class Config:
        from_attributes = True


class StylistByRating(BaseModel):
    average_rating: float
    limit: int = 10
    offset: int = 0



class StylistFilteredResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    bio: str
    specialization: str
    average_rating: str
    limit: int = 10
    offset: int = 0
    services: List[ServiceResponse]  # This represents the related services for each stylist

    class Config:
        from_attributes = True
######################################################

class BookingCreate(BaseModel):
    stylist_id: int
    service_id: int
    appointment_time: datetime


    @validator("appointment_time")
    def validate_appointment_time(cls, value):
        if value <= datetime.now(timezone.utc):
            raise ValueError("Appointment time must be in the future.")
        return value
    

class BookingCreateForUser(BaseModel):
    user_id: int
    stylist_id: int
    service_id: int
    appointment_time: datetime


    @validator("appointment_time")
    def validate_appointment_time(cls, value):
        if value <= datetime.now(timezone.utc):
            raise ValueError("Appointment time must be in the future.")
        return value


class BookingUpdate(BookingCreate):
    pass

class BookingResponse(BaseModel):
    id: int
    user_id: int
    stylist_id: int
    service_id: int
    appointment_time: datetime
    status: str
    stylist_name: str
    service_name: str

    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    previous_bookings: List[BookingResponse]
    upcoming_bookings: List[BookingResponse]

##########################################################

class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime 
##############################################################

class UserValidationSchema(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str = "admin"

#########################################################

class ReviewCreate(BaseModel):
    stylist_id: int
    rating: condecimal(ge=1, le=5)  # type: ignore # Ensures the rating is between 1 and 5
    review_text: Optional[str] = None  # Optional text review

    class Config:
        from_attributes = True

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    stylist_id: int
    rating: float
    created_at: datetime
    review_text: Optional[str] = None

    class Config:
        from_attributes = True