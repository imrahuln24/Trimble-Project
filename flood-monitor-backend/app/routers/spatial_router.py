# app/routers/spatial_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/spatial",
    tags=["spatial analysis"],
    dependencies=[Depends(auth.get_current_active_user)] # Secure all spatial routes
)

@router.get("/sensors-in-radius", response_model=List[schemas.SensorDataOut])
async def get_sensors_within_radius_route( # Renamed
    latitude: float = Query(..., description="Center latitude for search", ge=-90, le=90),
    longitude: float = Query(..., description="Center longitude for search", ge=-180, le=180),
    radius_km: float = Query(..., gt=0, description="Search radius in kilometers"),
    min_water_level: Optional[float] = Query(None, description="Optional minimum water level filter"),
    db: Session = Depends(get_db)
):
    sensors_orm = crud.get_sensors_in_radius(
        db,
        lat=latitude,
        lon=longitude,
        radius_km=radius_km,
        water_level_threshold=min_water_level
    )
    return sensors_orm

@router.get("/risk-map-data", response_model=List[schemas.RiskPoint])
async def get_dynamic_risk_map_data_route(db: Session = Depends(get_db)): # Renamed
    latest_sensor_readings = crud.get_sensor_data_for_risk_map(db, limit=200) # Fetches models.SensorData
    risk_points = []
    for sensor_orm in latest_sensor_readings:
        risk_level = "low"
        if sensor_orm.water_level is not None:
            if sensor_orm.water_level > 7.0: risk_level = "high"
            elif sensor_orm.water_level > 5.0: risk_level = "medium"
        
        risk_points.append(
            schemas.RiskPoint(
                latitude=sensor_orm.latitude,
                longitude=sensor_orm.longitude,
                water_level=sensor_orm.water_level,
                risk_level=risk_level,
                sensor_id=sensor_orm.sensor_id,
                last_updated=sensor_orm.timestamp
            )
        )
    return risk_points
'''
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional # Make sure Optional is imported
from app import crud, models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/spatial",
    tags=["spatial analysis"],
)

@router.get("/sensors-in-radius", response_model=List[schemas.SensorDataOut]) # Changed to SensorDataOut
async def get_sensors_within_radius_endpoint(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(..., gt=0),
    min_water_level: Optional[float] = Query(None), # Match mapService.js param
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    sensors_orm = crud.get_sensors_in_radius(
        db,
        lat=latitude,
        lon=longitude,
        radius_km=radius_km,
        water_level_threshold=min_water_level
    )
    return sensors_orm

@router.get("/risk-map-data", response_model=List[schemas.RiskPoint])
async def get_dynamic_risk_map_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    latest_sensor_readings = crud.get_sensor_data_for_risk_map(db) # Fetches models.SensorData
    risk_points = []
    for sensor_orm in latest_sensor_readings:
        risk_level = "low"
        # Ensure sensor_orm.water_level is not None before comparison
        if sensor_orm.water_level is not None:
            if sensor_orm.water_level > 7.0:
                risk_level = "high"
            elif sensor_orm.water_level > 5.0:
                risk_level = "medium"
        
        risk_points.append(
            schemas.RiskPoint( # Directly create Pydantic model
                latitude=sensor_orm.latitude,
                longitude=sensor_orm.longitude,
                water_level=sensor_orm.water_level,
                risk_level=risk_level,
                sensor_id=sensor_orm.sensor_id,
                last_updated=sensor_orm.timestamp # Added last_updated from timestamp
            )
        )
    return risk_points


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/spatial",
    tags=["spatial analysis"],
)

@router.post("/sensors-in-radius", response_model=List[schemas.SensorLocation])
async def get_sensors_within_radius_endpoint(
    query: schemas.SpatialQueryCircle,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Auth
):
    # Permissions check can be added here if needed
    # e.g., if current_user.role not in [schemas.RoleEnum.COMMANDER, schemas.RoleEnum.ADMIN]:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
    sensors = crud.get_sensors_in_radius(
        db,
        lat=query.latitude,
        lon=query.longitude,
        radius_km=query.radius_km
    )
    if not sensors:
        # It's not an error if no sensors are found, just return an empty list.
        # Consider if an error should be raised for very large radii or other invalid inputs.
        pass
    
    # Convert to SensorLocation schema for output, which is simpler than full SensorDataOut
    return [schemas.SensorLocation.from_orm(s) for s in sensors]

@router.get("/risk-map-data", response_model=List[schemas.RiskPoint])
async def get_dynamic_risk_map_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Auth
):
    latest_sensor_readings = crud.get_latest_sensor_data_for_risk_map(db)
    risk_points = []
    for sensor in latest_sensor_readings:
        risk_level = "low"
        if sensor.water_level > 7.0: # Critical threshold
            risk_level = "high"
        elif sensor.water_level > 5.0: # Warning threshold
            risk_level = "medium"
        
        risk_points.append(
            schemas.RiskPoint(
                latitude=sensor.latitude,
                longitude=sensor.longitude,
                water_level=sensor.water_level,
                risk_level=risk_level,
                sensor_id=sensor.sensor_id
            )
        )
    return risk_points
'''