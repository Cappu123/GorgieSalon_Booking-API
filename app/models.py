from .database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, TIMESTAMP, Table, DateTime
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
    bookings = relationship("Booking", back_populates="user")


stylist_service_association = Table(
    'stylist_service', Base.metadata,
    Column('stylist_id', Integer, ForeignKey('stylists.id'), primary_key=True),
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True)
)


class Stylist(Base):
    """Stylists model"""
    __tablename__ = 'stylists'

    id = Column(Integer, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="stylist", nullable=False)
    bio = Column(Text)
    specialization = Column(String)
    verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), 
                        nullable=False, server_default=text('now()'))

    # Relationships
    bookings = relationship("Booking", back_populates="stylist")
    services = relationship("Service", secondary=stylist_service_association, back_populates="stylists")
    #appointments = relationship("Appointment", secondary=stylist_appointments, 
                    #            back_populates="stylists")



class Service(Base):
    """Services model"""
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)  
    duration = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), 
                        nullable=False, server_default=text('now()'))

    # Many-to-Many relationship with stylists
    bookings = relationship("Booking", back_populates="service")
    stylists = relationship("Stylist", secondary=stylist_service_association, back_populates="services") 



class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    stylist_id = Column(Integer, ForeignKey('stylists.id'), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # Example statuses: "pending", "confirmed", "completed"

    user = relationship("User", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    stylist = relationship("Stylist", back_populates="bookings")


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
    appointment_id = Column(Integer, ForeignKey('appointments.id'))
    rating = Column(Integer)  # Rating out of 5
    comments = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))


