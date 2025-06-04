from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base # Use declarative_base once
import enum

# Define Base ONCE for all models
Base = declarative_base()

class RoleEnum(str, enum.Enum):
    admin = "admin"
    field_responder = "field_responder"
    commander = "commander"
    government_official = "government_official"
    viewer = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLAlchemyEnum(RoleEnum), nullable=False) # Use SQLAlchemy Enum for DB consistency
    
    messages = relationship("Message", back_populates="user")


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    water_level = Column(Float)
    rainfall = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    level = Column(String, nullable=False)  # e.g. info, warning, critical
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_resolved = Column(Boolean, default=False)
    sensor_id = Column(String, index=True, nullable=True) # Optional: link alert to a sensor


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="messages")


'''

from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    water_level = Column(Float)
    rainfall = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Column, Integer, String, Enum
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    responder = "responder"
    viewer = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String)
    
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    level = Column(String, nullable=False)  # e.g. info, warning, critical
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_resolved = Column(Boolean, default=False)
    '''