from pydantic import BaseModel, EmailStr
from datetime import datetime, time
from enum import Enum
from typing import List, Literal

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

class StylistCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    bio: str
    specialization: str
    service_id: List[int] #List of serivces.service_id


class ServiceCreate(BaseModel):
    service_id: int
    name: str
    description: str
    duration: float
    price: float


#######################################################


class StylistResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    bio: str
    services: List[ServiceCreate]



class ServiceResponse(BaseModel):
    id: int
    service_id: int
    name: str
    description: str
    duration: float
    price: float
    created_at: datetime
    stylists: List[StylistResponse]



######################################################

class BookingCreate(BaseModel):
    stylist_id: int
    service_id: int
    appointment_time: datetime


class BookingResponse(BookingCreate):
    id: int
    user_id: int
    service_id: int
    stylist_id: int
    appointment_time: datetime
    status: str

    class Config:
        from_attributes = True


class BookingStatusUpdate(BaseModel):
    status: Literal["accepted", "rejected"]

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