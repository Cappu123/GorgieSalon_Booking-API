from pydantic import BaseModel, EmailStr
from datetime import datetime, time
from enum import Enum
from typing import List


class UserBase(BaseModel):
    email: EmailStr
    username: str
    password: str

    class Config:
        use_enum_values = True
        from_attributes = True


class UserCreate(UserBase):
    pass


class UserResponseBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        use_enum_values = True
        from_attributes = True


class UserCreateResponse(UserResponseBase):
    pass

  

class Service(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class StylistCreate(UserBase):
    gender: str
    bio: str
    specialization: str
    services: List[Service]

    class Config:
        from_attributes = True


class StylistCreateResponse(UserBase):
    bio: str
    gender: str
    specialization: str
    services: List[Service]
    verified: bool = False
    is_active: bool = False

    class Config:
        from_attributes = True

class StylistwithServicesResponse(StylistCreateResponse):

    services: List[Service]


class TokenData(BaseModel):
    username: str

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

class AppointmentResponse(BaseModel):
    client_name: str
    stylist_name: str
    scheduled_time: datetime
    service_type: str
    status: str

    class Config:
        from_attributes = True


class ServiceResponse(BaseModel):
    id: int
    description: str
    price: float
    duration: int

    class Config:
        from_attributes = True


class StylistDashboardResponse(BaseModel):
    profile: StylistCreateResponse
    appointments: list[AppointmentResponse]
    services: list[ServiceResponse]

    class Config:
        from_attributes = True



class BookingCreate(BaseModel):
    client_id: int
    stylist_id: int
    service_id: int
    date: datetime
    time_slot: time
    status: str


class BookingResponse(BookingCreate):
    pass