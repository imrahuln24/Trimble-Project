# app/routers/sensor_router.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from app import crud, models, schemas, auth # auth might not be needed if endpoint is internal/unprotected
from app.database import get_db
from app.websocket_manager import manager as connection_manager # For broadcasting
# Removed: from .. import models, schemas, crud, database (avoid .. imports if possible, use app.)

router = APIRouter(
    # No prefix here if we want /sensor-data directly.
    # If prefixed with /sensor, then paths become /sensor/ingest and /sensor/data
    # For now, let's assume sensor_router handles all sensor-related HTTP,
    # and main.py handles the general WebSocket.
    tags=["sensor data"], # General tag
)

# --- Sensor Data Ingestion (POST) ---
@router.post("/sensor-ingest", response_model=schemas.SensorDataOut, status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data_route( # Renamed function
    data: schemas.SensorDataCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    # Optional: Add auth if sensors need to authenticate
    # current_user: models.User = Depends(auth.role_checker([schemas.RoleEnum.admin, schemas.RoleEnum.field_responder]))
):
    try:
        sensor_entry_orm = crud.create_sensor_data(db=db, data=data)

        sensor_out = schemas.SensorDataOut.model_validate(sensor_entry_orm)
        background_tasks.add_task(
            connection_manager.broadcast_general,
            {"type": "sensor_update", "data": sensor_out.model_dump(mode='json')}
        )

        # Alert checking (from your existing code)
        if sensor_entry_orm.water_level is not None:
            alert_to_create = None
            if sensor_entry_orm.water_level > 7.0:
                alert_to_create = schemas.AlertCreate(
                    title=f"Critical Water Level at Sensor {sensor_entry_orm.sensor_id}",
                    description=f"Water level reached {sensor_entry_orm.water_level:.2f}m.",
                    level="critical", sensor_id=sensor_entry_orm.sensor_id
                )
            elif sensor_entry_orm.water_level > 5.0:
                alert_to_create = schemas.AlertCreate(
                    title=f"Warning: High Water Level at Sensor {sensor_entry_orm.sensor_id}",
                    description=f"Water level at {sensor_entry_orm.water_level:.2f}m.",
                    level="warning", sensor_id=sensor_entry_orm.sensor_id
                )
            
            if alert_to_create:
                db_alert = crud.create_alert_db(db=db, alert=alert_to_create)
                background_tasks.add_task(
                    connection_manager.broadcast_general,
                    {"type": "new_alert", "data": schemas.AlertOut.model_validate(db_alert).model_dump(mode='json')}
                )

        return sensor_entry_orm
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# --- Get Latest Sensor Data (for LiveMap initial load) ---
@router.get("/sensor-data", response_model=List[schemas.SensorDataOut])
def get_latest_sensor_data_route( # Renamed function
    limit: int = Query(50, ge=1, le=200), # Default limit 50 for LiveMap
    db: Session = Depends(get_db),
    # Optional: Add auth if this data needs protection
    # current_user: models.User = Depends(auth.get_current_active_user)
):
    return crud.get_latest_sensor_data(db, limit=limit)

'''
# app/routers/sensor_router.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, models, schemas, auth # auth might not be needed if endpoint is internal/unprotected
from app.database import get_db
from app.websocket_manager import manager as connection_manager # For broadcasting
from .. import models, schemas, crud, database
from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter(
    prefix="/sensor-ingest", # Using a different prefix to avoid conflict with /sensor-data for GET
    tags=["sensor data ingestion"],
)

# Function to check for alerts (example logic)
def check_and_create_alerts(db: Session, sensor_data: models.SensorData, background_tasks: BackgroundTasks):
    alert_created = False
    if sensor_data.water_level is not None:
        if sensor_data.water_level > 7.0: # Critical threshold
            alert_data = schemas.AlertCreate(
                title=f"Critical Water Level at Sensor {sensor_data.sensor_id}",
                description=f"Water level reached {sensor_data.water_level:.2f}m.",
                level="critical", # or "high"
                sensor_id=sensor_data.sensor_id
            )
            db_alert = crud.create_alert_db(db=db, alert=alert_data)
            background_tasks.add_task(
                connection_manager.broadcast_general,
                {"type": "new_alert", "data": schemas.AlertOut.model_validate(db_alert).model_dump(mode='json')}
            )
            alert_created = True
        elif sensor_data.water_level > 5.0: # Warning threshold
            alert_data = schemas.AlertCreate(
                title=f"Warning: High Water Level at Sensor {sensor_data.sensor_id}",
                description=f"Water level at {sensor_data.water_level:.2f}m.",
                level="warning", # or "medium"
                sensor_id=sensor_data.sensor_id
            )
            db_alert = crud.create_alert_db(db=db, alert=alert_data)
            background_tasks.add_task(
                connection_manager.broadcast_general,
                {"type": "new_alert", "data": schemas.AlertOut.model_validate(db_alert).model_dump(mode='json')}
            )
            alert_created = True
    # Add more alert conditions (e.g., for rainfall)
    return alert_created


@router.post("/", response_model=schemas.SensorDataOut, status_code=status.HTTP_201_CREATED)
async def ingest_sensor_data(
    data: schemas.SensorDataCreate,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
    # Add API Key auth here if this endpoint is exposed externally for sensors
    # current_user: models.User = Depends(auth.get_current_active_user) # Or specific role/API key
):
    try:
        sensor_entry_orm = crud.create_sensor_data(db=db, data=data)

        # Broadcast new sensor data
        sensor_out = schemas.SensorDataOut.model_validate(sensor_entry_orm)
        background_tasks.add_task(
            connection_manager.broadcast_general,
            {"type": "sensor_update", "data": sensor_out.model_dump(mode='json')}
        )

        # Check for alerts based on the new data
        check_and_create_alerts(db, sensor_entry_orm, background_tasks)

        return sensor_entry_orm # FastAPI handles serialization
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Endpoint to get existing sensor data (already in main.py, could be moved here)
@router.get("/data", response_model=List[schemas.SensorDataOut])
def get_all_sensor_data(
    limit: int = 100,
    db: Session = Depends(get_db),
    # current_user: models.User = Depends(auth.get_current_active_user) # Secure if needed
):
    return crud.get_latest_sensor_data(db, limit=limit)

# General WebSocket endpoint (moved from main.py)
@router.websocket("/ws/general") # Path relative to router prefix, e.g. /sensor-ingest/ws/general
async def websocket_general_endpoint(websocket: WebSocket):
    # Or if you want it at /ws/general, define it in main.py or a router with no prefix
    await connection_manager.connect(websocket, connection_type="general")
    try:
        while True:
            await websocket.receive_text() # Keep connection open
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, connection_type="general")
    except Exception as e:
        print(f"General WebSocket error in sensor_router: {e}")
        connection_manager.disconnect(websocket, connection_type="general")

# Make sure the /sensor-data GET endpoint is here:
@router.get("/data", response_model=List[schemas.SensorDataOut]) # Path: /sensor-ingest/data
def get_all_sensor_data_from_router( # Renamed to avoid conflict if you had one in main.py
    limit: int = 100,
    db: Session = Depends(database.get_db),
):
    return crud.get_latest_sensor_data(db, limit=limit)
    '''