from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func 
from . import models, schemas
# Import get_password_hash from the new security.py
from .security import get_password_hash
from typing import Optional

# SensorData CRUD
def create_sensor_data(db: Session, data: schemas.SensorDataCreate) -> models.SensorData:
    sensor_entry = models.SensorData(**data.model_dump()) # Use model_dump() for Pydantic v2
    db.add(sensor_entry)
    db.commit()
    db.refresh(sensor_entry)
    return sensor_entry

def get_latest_sensor_data(db: Session, limit: int = 100) -> list[models.SensorData]:
    return db.query(models.SensorData).order_by(models.SensorData.timestamp.desc()).limit(limit).all()

def get_sensor_data_for_risk_map(db: Session, limit: int = 500) -> list[models.SensorData]:
    subquery = db.query(
        models.SensorData.sensor_id,
        func.max(models.SensorData.timestamp).label("max_timestamp")
    ).group_by(models.SensorData.sensor_id).subquery()

    return db.query(models.SensorData).join(
        subquery,
        (models.SensorData.sensor_id == subquery.c.sensor_id) &
        (models.SensorData.timestamp == subquery.c.max_timestamp)
    ).order_by(models.SensorData.timestamp.desc()).limit(limit).all()


# User CRUD
def get_user(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password) # Uses get_password_hash from security.py
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password, 
        role=user.role # SQLAlchemy Enum will handle the string value from Pydantic Enum
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Alert CRUD
def create_alert_db(db: Session, alert: schemas.AlertCreate) -> models.Alert:
    db_alert = models.Alert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

def get_alerts_db(db: Session, skip: int = 0, limit: int = 100) -> list[models.Alert]:
    return db.query(models.Alert).order_by(desc(models.Alert.timestamp)).offset(skip).limit(limit).all()

def get_latest_unresolved_alerts(db: Session, count: int = 2) -> list[models.Alert]:
    return db.query(models.Alert)\
        .filter(models.Alert.is_resolved == False)\
        .order_by(models.Alert.timestamp.desc())\
        .limit(count)\
        .all()

def resolve_alert_db(db: Session, alert_id: int) -> Optional[models.Alert]:
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if alert:
        alert.is_resolved = True
        db.commit()
        db.refresh(alert)
    return alert

from sqlalchemy.orm import Session, joinedload # Ensure joinedload is imported

# ...

# Message (Chat) CRUD
def create_message(db: Session, message: schemas.MessageCreate, user_id: int) -> models.Message:
    db_message = models.Message(**message.model_dump(), user_id=user_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    # Eager load user for username in MessageOut, especially for WebSocket broadcast
    # Use a new query to ensure the refreshed object includes the relationship
    return db.query(models.Message).options(joinedload(models.Message.user)).filter(models.Message.id == db_message.id).one()


def get_messages(db: Session, skip: int = 0, limit: int = 50) -> list[models.Message]:
    return db.query(models.Message)\
        .options(joinedload(models.Message.user)) \
        .order_by(models.Message.timestamp.asc()) \
        .offset(skip)\
        .limit(limit)\
        .all()

# Spatial Analysis (Haversine-based, simplified)
from math import radians, sin, cos, sqrt, atan2
from typing import Optional # Ensure this is imported if not already

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # Radius of Earth in kilometers

    lat1_rad, lon1_rad = radians(lat1), radians(lon1)
    lat2_rad, lon2_rad = radians(lat2), radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance

def get_sensors_in_radius(db: Session, lat: float, lon: float, radius_km: float, water_level_threshold: Optional[float] = None) -> list[models.SensorData]:
    # Consider fetching only latest reading per sensor if dataset is large
    all_latest_sensors = get_sensor_data_for_risk_map(db, limit=1000) # Adjust limit as needed
    nearby_sensors = []
    for sensor in all_latest_sensors:
        if sensor.latitude is not None and sensor.longitude is not None:
            distance = haversine(lat, lon, sensor.latitude, sensor.longitude)
            if distance <= radius_km:
                if water_level_threshold is None or (sensor.water_level is not None and sensor.water_level >= water_level_threshold):
                    nearby_sensors.append(sensor)
    return nearby_sensors


'''
from sqlalchemy.orm import Session
from . import models, schemas

def create_sensor_data(db: Session, data: schemas.SensorDataCreate):
    sensor_entry = models.SensorData(**data.dict())
    db.add(sensor_entry)
    db.commit()
    db.refresh(sensor_entry)
    return sensor_entry

def get_latest_sensor_data(db: Session, limit: int = 100):
    return db.query(models.SensorData).order_by(models.SensorData.timestamp.desc()).limit(limit).all()
    '''
