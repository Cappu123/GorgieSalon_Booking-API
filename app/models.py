from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, TIMESTAMP, Table, DateTime
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
from enum import Enum
from pydantic import BaseModel, EmailStr
from datetime import datetime
import datetime
from typing import List
from sqlalchemy.dialects.postgresql import ARRAY


# Association tables for many-to-many relationships
class StylistService(Base):
    """stylist_services association model"""
    __tablename__ = 'stylist_services'
    stylist_id = Column(Integer, ForeignKey('stylists.id', ondelete="CASCADE"), primary_key=True)
    service_id = Column(Integer, ForeignKey('services.service_id', ondelete="CASCADE"), primary_key=True)



class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="client", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # Relationships
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")

class Stylist(Base):
    """Stylists model"""
    __tablename__ = 'stylists'

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="stylist", nullable=False)
    bio = Column(String, default="stylist", nullable=False)
    specialization = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), 
                        nullable=False, server_default=text('now()'))

    # Relationships
    bookings = relationship("Booking", back_populates="stylist", cascade="all, delete-orphan")
    services = relationship("Service", secondary="stylist_services", back_populates="stylists")


class Service(Base):
    """Services model"""
    __tablename__ = 'services'

    service_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)  
    duration = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Many-to-Many relationship with stylists
    bookings = relationship("Booking", back_populates="service", cascade="all, delete-orphan")
    stylists = relationship("Stylist", secondary="stylist_services", back_populates="services")


class Booking(Base):
    """Booking model"""
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stylist_id = Column(Integer, ForeignKey("stylists.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.service_id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # Status options: "pending", "confirmed", "completed"

    # Relationships
    user = relationship("User", back_populates="bookings")
    stylist = relationship("Stylist", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")

    
class Admin(Base):
    """Admin model"""
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="admin")
    email = Column(String, unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))


class Review(Base):
    """Review model"""
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    rating = Column(Integer)  # Rating out of 5
    comments = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))