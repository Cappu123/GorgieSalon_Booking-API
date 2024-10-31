from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from enum import Enum
from pydantic import BaseModel, EmailStr
from datetime import datetime


class User(Base):
    """User base model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="client")
    email = Column(String, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # Relationships
    stylist_profile = relationship("Stylist", back_populates="user", uselist=False)
    appointments = relationship("Appointment", back_populates="client")


class Stylist(Base):
    """Stylists model"""
    __tablename__ = 'stylists'

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="stylist")
    bio = Column(Text)
    specialization = Column(String)
    verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), 
                        nullable=False, server_default=text('now()'))

    # Relationships
    user = relationship("User", back_populates="stylist_profile")
    services = relationship("Service", secondary="stylist_services", back_populates="stylists")
    appointments = relationship("Appointment", back_populates="stylist")


class StylistServices(Base):
    __tablename__ = 'stylist_services'
    stylist_id = Column(Integer, ForeignKey("stylists.id"), primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), primary_key=True)

class Admin(Base):
    """Admin model"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="admin")
    email = Column(String, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

class Service(Base):
    """Services model"""
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    duration = Column(Integer, nullable=False)

    # Many-to-Many relationship with stylists
    stylists = relationship("Stylist", secondary="stylist_services", back_populates="services")


class Appointment(Base):
    """Appointments model"""
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, nullable=False)
    stylist_id = Column(Integer, ForeignKey('stylists.id'))
    client_id = Column(Integer, ForeignKey('users.id'))
    appointment_time = Column(TIMESTAMP(timezone=True))
    duration = Column(Integer, nullable=False)
    status = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    stylist = relationship("Stylist", back_populates="appointments")
    client = relationship("User", back_populates="appointments")
    review = relationship("Review", back_populates="appointment", uselist=False)


class Review(Base):
    """Review model"""
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'))
    rating = Column(Integer)  # Rating out of 5
    comments = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

    # Relationship
    appointment = relationship("Appointment", back_populates="review")
