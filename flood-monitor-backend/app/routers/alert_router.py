from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, models, schemas, auth
from app.database import get_db
# Use the global manager instance from websocket_manager
from app.websocket_manager import manager as connection_manager

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)

# Helper for formatting new alerts for WebSocket broadcast
def format_new_alert_for_broadcast(alert_orm: models.Alert) -> dict:
    alert_out = schemas.AlertOut.model_validate(alert_orm) # Pydantic V2
    return {"type": "new_alert", "data": alert_out.model_dump(mode='json')}

# Helper for formatting resolved alerts for WebSocket broadcast
def format_resolved_alert_for_broadcast(alert_orm: models.Alert) -> dict:
    alert_out = schemas.AlertOut.model_validate(alert_orm) # Pydantic V2
    return {"type": "alert_resolved", "data": alert_out.model_dump(mode='json')}


@router.post("/", response_model=schemas.AlertOut, status_code=status.HTTP_201_CREATED)
async def create_alert_endpoint(
    alert_data: schemas.AlertCreate, # Use AlertCreate from schemas
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    allowed_roles = [
        schemas.RoleEnum.admin, # Direct Pydantic enum value
        schemas.RoleEnum.commander,
        schemas.RoleEnum.field_responder
    ]
    # current_user.role is SQLAlchemy enum, its .value is string. schemas.RoleEnum is Pydantic enum.
    if schemas.RoleEnum(current_user.role.value) not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create alerts")

    # crud.create_alert_db expects schemas.AlertCreate
    db_alert = crud.create_alert_db(db=db, alert=alert_data)

    # Broadcast new alert
    background_tasks.add_task(
        connection_manager.broadcast_general,
        format_new_alert_for_broadcast(db_alert)
    )
    return db_alert # FastAPI handles serialization using AlertOut.model_validate


@router.get("/", response_model=List[schemas.AlertOut])
def get_alerts_endpoint(
    # resolved: Optional[bool] = None, # crud.get_alerts_db needs update for this
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # Modify crud.get_alerts_db if filtering by 'resolved' is needed.
    # For now, removing the 'resolved' filter argument from the call.
    alerts = crud.get_alerts_db(db, skip=skip, limit=limit)
    return alerts # FastAPI handles serialization

# Endpoint for AlertNotifications.js
@router.get("/latest-unresolved", response_model=List[schemas.AlertOut])
def get_latest_unresolved_alerts_endpoint(
    count: int = 2, # Match default in AlertNotifications.js
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Auth recommended
):
    alerts = crud.get_latest_unresolved_alerts(db, count=count)
    return alerts


@router.get("/{alert_id}", response_model=schemas.AlertOut)
def get_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    # crud.get_alert_db needs to be defined. Assuming it looks like:
    # def get_alert_db(db: Session, alert_id: int) -> Optional[models.Alert]:
    #     return db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    db_alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first() # Temporary direct query
    if db_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return db_alert


@router.put("/{alert_id}/resolve", response_model=schemas.AlertOut)
async def resolve_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.role_checker([
        schemas.RoleEnum.commander,
        schemas.RoleEnum.field_responder,
        schemas.RoleEnum.admin
    ])),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # crud.resolve_alert_db expects alert_id, not the ORM object.
    # crud.resolve_alert_db needs to handle user_id if you plan to log who resolved it.
    # For now, adapting to the provided crud.resolve_alert_db signature.
    
    # Fetch the alert first to check its existence and current state
    alert_to_resolve = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if alert_to_resolve is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert_to_resolve.is_resolved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert already resolved")

    resolved_alert_orm = crud.resolve_alert_db(db=db, alert_id=alert_id) # Pass alert_id
    if not resolved_alert_orm: # Should not happen if checks above pass, but good practice
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve alert")

    # Broadcast updated alert status
    background_tasks.add_task(
        connection_manager.broadcast_general,
        format_resolved_alert_for_broadcast(resolved_alert_orm)
    )
    return resolved_alert_orm

'''
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app import crud, models, schemas, auth
from app.database import get_db
from app.websocket_manager import sensor_manager # For broadcasting alert updates

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)

def format_alert_for_broadcast(alert: models.Alert):
    # Ensure the alert object is serializable, e.g., convert to dict if needed
    # Using Pydantic model for serialization is safer
    alert_out = schemas.AlertOut.from_orm(alert)
    return {"type": "alert_update", "data": alert_out.model_dump()}


@router.post("/", response_model=schemas.AlertOut, status_code=status.HTTP_201_CREATED)
async def create_alert_endpoint(
    alert_data: schemas.AlertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user), # Ensure auth
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    # Permissions check (example: only certain roles can create alerts manually)
    if current_user.role not in [schemas.RoleEnum.ADMIN, schemas.RoleEnum.COMMANDER, schemas.RoleEnum.FIELD_RESPONDER]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create alerts")

    db_alert = crud.create_alert_db(db=db, alert_data=alert_data)
    
    # Broadcast new alert
    background_tasks.add_task(sensor_manager.broadcast, format_alert_for_broadcast(db_alert))
    
    return db_alert


@router.get("/", response_model=List[schemas.AlertOut])
def get_alerts_endpoint(
    resolved: Optional[bool] = None, # Filter by resolved status
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Auth recommended
):
    alerts = crud.get_alerts_db(db, skip=skip, limit=limit, resolved=resolved)
    return alerts


@router.get("/{alert_id}", response_model=schemas.AlertOut)
def get_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Auth recommended
):
    db_alert = crud.get_alert_db(db, alert_id=alert_id)
    if db_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return db_alert


@router.put("/{alert_id}/resolve", response_model=schemas.AlertOut)
async def resolve_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.role_checker([schemas.RoleEnum.COMMANDER, schemas.RoleEnum.FIELD_RESPONDER, schemas.RoleEnum.ADMIN])),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    db_alert = crud.get_alert_db(db, alert_id=alert_id)
    if db_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if db_alert.is_resolved:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert already resolved")

    resolved_alert = crud.resolve_alert_db(db=db, alert=db_alert, user_id=current_user.id)
    
    # Broadcast updated alert status
    background_tasks.add_task(sensor_manager.broadcast, format_alert_for_broadcast(resolved_alert))
    
    return resolved_alert
'''