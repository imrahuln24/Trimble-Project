# app/main.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
# If DebugCORSMiddleware is not strictly needed for current debugging, simplify to Starlette's
# from starlette.requests import Request
# from starlette.responses import Response
# from starlette.types import ASGIApp, Receive, Scope, Send

from . import models, schemas, crud, database
from .database import engine # SessionLocal removed as get_db from database.py is preferred
from .websocket_manager import manager # Global manager
from .auth import get_current_active_user, get_current_user, authenticate_user # role_checker used in routers
from .security import create_access_token

# Import Routers
from .routers import alert_router, chat_router, spatial_router, sensor_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flood Monitoring API")

# --- CORS Middleware ---
# Using Starlette's directly for simplicity now.
# Replace with DebugCORSMiddleware if specific debugging printouts are still needed.
app.add_middleware(
    StarletteCORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Authentication Endpoints ---
@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.UserOut)
def register_user_main(user: schemas.UserCreate, db: Session = Depends(database.get_db)): # Renamed to avoid conflict if any
    print(f"INFO: Received registration request for username: {user.username}, role: {user.role.value}")
    db_user = crud.get_user(db, user.username)
    if db_user:
        print(f"WARNING: Username '{user.username}' already registered.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    try:
        created_user = crud.create_user(db=db, user=user)
        print(f"INFO: User '{created_user.username}' created successfully with ID: {created_user.id} and role: {created_user.role.value}")
        return created_user
    except Exception as e:
        print(f"ERROR: Failed to create user '{user.username}'. Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {str(e)}")

@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me_main(current_user: models.User = Depends(get_current_active_user)): # Renamed
    return current_user

# --- Root Endpoint ---
@app.get("/")
def root_main(): # Renamed
    return {"message": "Flood Monitoring API is operational"}

# --- General WebSocket Endpoint (Public, no auth needed by default) ---
@app.websocket("/ws/general")
async def websocket_general_endpoint_main(websocket: WebSocket): # Renamed
    await manager.connect(websocket, connection_type="general")
    print(f"General WebSocket connected: {websocket.client}")
    try:
        while True:
            # You might want to handle incoming messages or just keep alive
            data = await websocket.receive_text()
            print(f"Received on /ws/general: {data} (usually not expected for one-way broadcast)")
    except WebSocketDisconnect:
        manager.disconnect(websocket, connection_type="general")
        print(f"General WebSocket disconnected: {websocket.client}")
    except Exception as e:
        print(f"Error in /ws/general for {websocket.client}: {e}")
        manager.disconnect(websocket, connection_type="general")


# --- Include Routers (These handle their own prefixed paths) ---
# The /sensor-data GET endpoint and /risk-map-data GET endpoint
# should be defined within sensor_router.py and spatial_router.py respectively.

app.include_router(sensor_router.router) # Handles /sensor-ingest/* (and potentially /sensor-data if defined there)
app.include_router(alert_router.router)   # Handles /alerts/*
app.include_router(chat_router.router)    # Handles /chat/*
app.include_router(spatial_router.router) # Handles /spatial/*


'''
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Query, status # Added status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

from . import models, schemas, crud, database
from .database import engine, SessionLocal # Base is in models
from .websocket_manager import manager
# Import from auth for authentication logic and user retrieval
from .auth import get_current_active_user, role_checker, get_current_user, authenticate_user
# Import from security for token creation
from .security import create_access_token

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flood Monitoring API")

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Flood Monitoring API is operational"}

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional

# Import Starlette's CORSMiddleware directly
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware
from starlette.requests import Request # For type hinting
from starlette.responses import Response # For type hinting
from starlette.types import ASGIApp, Receive, Scope, Send


from . import models, schemas, crud, database
from .database import engine, SessionLocal
from .websocket_manager import manager
from .auth import get_current_active_user, role_checker, get_current_user, authenticate_user
from .security import create_access_token
from .routers import alert_router, chat_router, spatial_router, sensor_router
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Flood Monitoring API")

# --- Custom Debugging CORS Middleware Wrapper ---
class DebugCORSMiddleware:
    def __init__(self, app: ASGIApp, **kwargs):
        self.app = app
        self.starlette_cors = StarletteCORSMiddleware(app, **kwargs) # Instantiate Starlette's
        print("DEBUG: DebugCORSMiddleware initialized with kwargs:", kwargs)

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and scope["method"] == "OPTIONS":
            print(f"DEBUG: OPTIONS request received for path: {scope.get('path')}")
            request_headers = dict(scope.get("headers", []))
            print(f"DEBUG: OPTIONS request headers: {request_headers}")
            
            # Define a new send function to intercept the response from Starlette's CORS
            async def send_wrapper(message):
                if message['type'] == 'http.response.start':
                    print(f"DEBUG: OPTIONS response from Starlette CORS - Status: {message.get('status')}, Headers: {message.get('headers')}")
                await send(message)
            
            try:
                # Call Starlette's CORS middleware directly
                await self.starlette_cors(scope, receive, send_wrapper)
                print(f"DEBUG: Starlette CORS middleware processed OPTIONS for {scope.get('path')}")
                return # Starlette's CORS should handle sending the response
            except Exception as e:
                print(f"DEBUG: Exception during Starlette CORS processing for OPTIONS: {e}")
                # Fallback to application if Starlette CORS has an issue or doesn't send response
                # This part might need refinement based on how Starlette's CORS handles things internally
        
        # For non-OPTIONS requests, or if OPTIONS wasn't fully handled above, pass to next in chain
        # (which would be Starlette's CORS if it didn't handle it, or the app itself)
        await self.starlette_cors(scope, receive, send)


# Apply the DebugCORSMiddleware
app.add_middleware(
    DebugCORSMiddleware, # Use our custom wrapper
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"], # Should include OPTIONS implicitly
    allow_headers=["*"],
)


# Dependency (can stay here or be in database.py only if routers import it from there)
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


@app.get("/")
def root():
    return {"message": "Flood Monitoring API is operational"}



@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)): # Use database.get_db
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)): # Use database.get_db
    print(f"INFO: Received registration request for username: {user.username}, role: {user.role.value}")
    db_user = crud.get_user(db, user.username) # crud.get_user is fine
    if db_user:
        print(f"WARNING: Username '{user.username}' already registered.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    try:
        created_user = crud.create_user(db=db, user=user) # crud.create_user is fine
        print(f"INFO: User '{created_user.username}' created successfully with ID: {created_user.id} and role: {created_user.role.value}")
        return created_user
    except Exception as e:
        print(f"ERROR: Failed to create user '{user.username}'. Exception: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {str(e)}")

@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

# --- Root Endpoint ---
@app.get("/")
def root():
    return {"message": "Flood Monitoring API is operational"}

# --- Include Routers (ALL OTHER ENDPOINTS SHOULD BE IN THESE ROUTERS) ---
app.include_router(sensor_router.router)
app.include_router(alert_router.router)
app.include_router(chat_router.router)
app.include_router(spatial_router.router)


@app.get("/sensor-data", response_model=List[schemas.SensorDataOut])
def read_main_sensor_data(limit: int = Query(100, ge=1, le=200), db: Session = Depends(database.get_db)): # Use Query for limit
    items = crud.get_latest_sensor_data(db=db, limit=limit)
    return items

# And ensure the /ws/general is also at root or adjust frontend
@app.websocket("/ws/general")
async def main_websocket_general_endpoint(websocket: WebSocket):
    await manager.connect(websocket, connection_type="general") # Use global manager from main.py context
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, connection_type="general")
    except Exception as e:
        print(f"General WebSocket error in main: {e}")
        manager.disconnect(websocket, connection_type="general")




# --- THE DEBUG /register ENDPOINT ---
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)): # Use schemas.UserCreate
    print(f"INFO: Received registration request for username: {user.username}, role: {user.role.value}") # Added log
    db_user = crud.get_user(db, user.username)
    if db_user:
        print(f"WARNING: Username '{user.username}' already registered.") # Added log
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    try:
        created_user = crud.create_user(db=db, user=user)
        print(f"INFO: User '{created_user.username}' created successfully with ID: {created_user.id} and role: {created_user.role.value}") # Added log
        return created_user
    except Exception as e:
        print(f"ERROR: Failed to create user '{user.username}'. Exception: {e}") # Added log
        # Log the full traceback for detailed debugging if needed
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {str(e)}")





@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password) # Uses authenticate_user from auth.py
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Uses create_access_token from security.py
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

# --- Sensor Data ---
@app.post("/sensor-data", response_model=schemas.SensorDataOut,
          dependencies=[Depends(role_checker([schemas.RoleEnum.admin, schemas.RoleEnum.field_responder]))])
async def post_sensor_data(
    data: schemas.SensorDataCreate,
    db: Session = Depends(get_db),
):
    sensor_reading = crud.create_sensor_data(db, data)

    await manager.broadcast_general({
        "type": "sensor_update",
        "payload": schemas.SensorDataOut.from_orm(sensor_reading).model_dump()
    })

    if data.water_level > 7.0: # Configurable threshold
        alert_data = schemas.AlertCreate(
            title=f"High Water Level at {data.sensor_id}",
            description=f"Water level is {data.water_level}m. Immediate attention required.",
            level="high",
            sensor_id=data.sensor_id
        )
        alert = crud.create_alert_db(db, alert_data)
        await manager.broadcast_general({
            "type": "new_alert",
            "payload": schemas.AlertOut.from_orm(alert).model_dump()
        })
    return sensor_reading

@app.get("/sensor-data", response_model=List[schemas.SensorDataOut])
def read_latest_sensor_data(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return crud.get_latest_sensor_data(db, limit=limit)

# --- Alerts ---
@app.post("/alerts/", response_model=schemas.AlertOut, status_code=status.HTTP_201_CREATED,
           dependencies=[Depends(role_checker([schemas.RoleEnum.admin, schemas.RoleEnum.commander]))])
async def create_new_alert(
    alert_data: schemas.AlertCreate, # Renamed from alert to avoid conflict
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_alert = crud.create_alert_db(db, alert_data)
    background_tasks.add_task(
        manager.broadcast_general,
        {"type": "new_alert", "payload": schemas.AlertOut.from_orm(db_alert).model_dump()}
    )
    return db_alert

@app.get("/alerts/latest-unresolved", response_model=List[schemas.AlertOut])
def get_latest_two_unresolved_alerts(db: Session = Depends(get_db)):
    return crud.get_latest_unresolved_alerts(db, count=2)

@app.get("/alerts/", response_model=List[schemas.AlertOut])
def get_all_alerts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return crud.get_alerts_db(db, skip=skip, limit=limit)


@app.put("/alerts/{alert_id}/resolve", response_model=schemas.AlertOut,
          dependencies=[Depends(role_checker([schemas.RoleEnum.admin, schemas.RoleEnum.commander, schemas.RoleEnum.field_responder]))])
async def resolve_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks() # Ensure default value
):
    alert = crud.resolve_alert_db(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    background_tasks.add_task(
        manager.broadcast_general,
        {"type": "alert_resolved", "payload": schemas.AlertOut.from_orm(alert).model_dump()}
    )
    return alert

# --- WebSockets ---
@app.websocket("/ws/general")
async def websocket_general_endpoint(websocket: WebSocket):
    await manager.connect(websocket, connection_type="general")
    try:
        while True:
            await websocket.receive_text() # Keep connection open, listen for pings if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, connection_type="general")
    except Exception as e:
        print(f"General WebSocket error: {e}")
        manager.disconnect(websocket, connection_type="general")


@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket, token: str = Query(...)):
    # Manually create a DB session for WebSocket auth as Depends doesn't work directly in signature for DB
    db = SessionLocal()
    try:
        user = await get_current_user(token=token, db=db) 
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        db.close()
        return
    finally:
        # db.close() # Close db if user not found or after use in this block
        # Keep db open for the duration of the chat if messages are to be saved
        pass


    await manager.connect(websocket, connection_type="chat")
    print(f"User {user.username} connected to chat.")
    try:
        while True:
            data = await websocket.receive_json()
            if "content" in data and isinstance(data["content"], str):
                message_create = schemas.MessageCreate(content=data["content"])
                # db session must be active here to save message
                db_message = crud.create_message(db, message_create, user_id=user.id)
                
                message_out = schemas.MessageOut(
                    id=db_message.id,
                    content=db_message.content,
                    user_id=db_message.user_id,
                    username=db_message.user.username,
                    timestamp=db_message.timestamp
                )
                await manager.broadcast_chat({
                    "type": "new_chat_message",
                    "payload": message_out.model_dump()
                })
            else:
                print(f"Received malformed chat data: {data}")

    except WebSocketDisconnect:
        print(f"User {user.username} disconnected from chat.")
    except Exception as e:
        print(f"Chat WebSocket error for {user.username}: {e}")
    finally:
        manager.disconnect(websocket, connection_type="chat")
        db.close() # Ensure DB session is closed when WebSocket connection ends


# --- Chat HTTP Endpoints ---
@app.get("/chat/messages", response_model=List[schemas.MessageOut],
         dependencies=[Depends(get_current_active_user)])
def get_chat_messages(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    messages = crud.get_messages(db, skip=skip, limit=limit)
    # Schema conversion should handle username from joinedload automatically if MessageOut.username is correctly typed
    return [schemas.MessageOut.from_orm(msg) for msg in messages]


# --- Risk Map and Spatial Analysis ---
def calculate_risk_level(water_level: Optional[float]) -> str:
    if water_level is None:
        return "unknown"
    if water_level > 7.0:
        return "high"
    elif water_level > 4.0:
        return "medium"
    else:
        return "low"

@app.get("/risk-map-data", response_model=List[schemas.RiskPoint],
          dependencies=[Depends(get_current_active_user)])
def get_risk_map_data(db: Session = Depends(get_db)):
    latest_sensor_data = crud.get_sensor_data_for_risk_map(db, limit=200)
    
    risk_points = []
    for sensor in latest_sensor_data:
        risk_points.append(schemas.RiskPoint(
            latitude=sensor.latitude,
            longitude=sensor.longitude,
            risk_level=calculate_risk_level(sensor.water_level),
            water_level=sensor.water_level,
            sensor_id=sensor.sensor_id,
            last_updated=sensor.timestamp
        ))
    return risk_points


@app.get("/spatial/sensors-in-radius", response_model=List[schemas.SensorDataOut],
          dependencies=[Depends(get_current_active_user)])
def get_spatial_sensors_in_radius(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(..., gt=0, description="Search radius in kilometers"),
    min_water_level: Optional[float] = Query(None, description="Minimum water level to filter by"),
    db: Session = Depends(get_db)
):
    # Validation is now handled by Pydantic/FastAPI Query parameters for lat/lon ranges
    sensors = crud.get_sensors_in_radius(db, latitude, longitude, radius_km, min_water_level)
    return sensors


from .routers import alert_router, chat_router, spatial_router, sensor_router # Add sensor_router


app.include_router(sensor_router.router) # Add this
app.include_router(alert_router.router)
app.include_router(chat_router.router)
app.include_router(spatial_router.router)

# Add the existing /sensor-data GET endpoint from LiveMap.js initial fetch
# Or move it to sensor_router.py
@app.get("/sensor-data", response_model=List[schemas.SensorDataOut])
def read_sensor_data(limit: int = 100, db: Session = Depends(get_db)):
    # This currently calls crud.get_latest_sensor_data
    # LiveMap.js fetches from /sensor-data?limit=50
    items = crud.get_latest_sensor_data(db=db, limit=limit)
    return items


from fastapi import WebSocket, WebSocketDisconnect
from .websocket_manager import ConnectionManager
from .auth import get_current_active_user
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import auth, models, schemas

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, crud
from .database import engine, SessionLocal, Base
from .schemas import SensorDataOut
from .alerts import Alert  # or wherever the Alert SQLAlchemy model is
from .alerts import AlertCreate, AlertOut  # adjust if your schema file has a different name
from app.alerts import router as alerts_router



#Base.metadata.create_all(bind=engine)

from app import models, database
from fastapi import FastAPI

models.Base.metadata.create_all(bind=database.engine)


app = FastAPI()
app.include_router(alerts_router)
# Allow React frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"message": "Flood Monitoring API working"}


@app.post("/sensor-data", response_model=schemas.SensorDataOut)
async def post_sensor_data(data: schemas.SensorDataCreate, db: Session = Depends(get_db)):
    # Save sensor reading
    sensor = crud.create_sensor_data(db, data)

    # Broadcast sensor data
    await manager.broadcast(schemas.SensorDataOut.from_orm(sensor).dict())

    # Trigger alert if water_level > 7
    if data.water_level > 7.0:
        alert = Alert(
            title=f"High Water Level at {data.sensor_id}",
            description=f"Water level is {data.water_level}m. Immediate attention required.",
            level="high"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        await manager.broadcast({
            "type": "alert",
            "alert": {
                "id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "level": alert.level,
                "timestamp": str(alert.timestamp),
                "is_resolved": alert.is_resolved,
            }
        })

    return sensor


@app.get("/sensor-data", response_model=list[schemas.SensorDataOut])
def read_data(db: Session = Depends(get_db)):
    return crud.get_latest_sensor_data(db)


manager = ConnectionManager()

@app.websocket("/ws/sensor")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)

from .auth import get_user
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username taken")
    hashed_pw = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pw, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/sensor-data", response_model=schemas.SensorDataOut)
async def post_sensor_data(
    data: schemas.SensorDataCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role not in ["admin", "responder"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    # Save sensor reading
    sensor = crud.create_sensor_data(db, data)

    # Broadcast sensor data
    await manager.broadcast(schemas.SensorDataOut.from_orm(sensor).dict())

    # Trigger alert if water_level > 7
    if data.water_level > 7.0:
        alert = Alert(
            title=f"High Water Level at {data.sensor_id}",
            description=f"Water level is {data.water_level}m. Immediate attention required.",
            level="high"
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        await manager.broadcast({
            "type": "alert",
            "alert": {
                "id": alert.id,
                "title": alert.title,
                "description": alert.description,
                "level": alert.level,
                "timestamp": str(alert.timestamp),
                "is_resolved": alert.is_resolved,
            }
        })

    return sensor

from fastapi.security import OAuth2PasswordRequestForm
from app.auth import authenticate_user, create_access_token

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


from fastapi import BackgroundTasks

@app.post("/alerts/", response_model=AlertOut)
async def create_alert(alert: AlertCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_alert = Alert(**alert.dict())
    db.add(db_alert)
    print("Adding alert to DB:", db_alert)
    db.commit()
    db.refresh(db_alert)

    background_tasks.add_task(manager.broadcast, {
        "type": "alert",
        "alert": {
            "id": db_alert.id,
            "title": db_alert.title,
            "description": db_alert.description,
            "level": db_alert.level,
            "timestamp": str(db_alert.timestamp),
            "is_resolved": db_alert.is_resolved,
        }
    })

    return db_alert
from typing import List

@app.get("/alerts/", response_model=List[AlertOut])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.timestamp.desc()).all()

@app.put("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    return alert

from sqlalchemy import func
from app.models import User

@app.get("/risk-map")
def get_risk_map(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return [{"latitude": 20.5, "longitude": 77.3, "risk": "high", "water_level": 8.5, "rainfall": 45.2}]


@app.get("/risk-map")
def get_risk_map(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role not in ["admin", "responder"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    print("Current user:", current_user.username, current_user.role)
    data = db.query(
        models.SensorData.latitude,
        models.SensorData.longitude,
        func.avg(models.SensorData.water_level).label("avg_water_level"),
        func.avg(models.SensorData.rainfall).label("avg_rainfall")
    ).group_by(
        models.SensorData.latitude, models.SensorData.longitude
    ).all()

    # Classify risk level
    result = []
    for row in data:
        risk = "low"
        if row.avg_water_level > 7 or row.avg_rainfall > 40:
            risk = "high"
        elif row.avg_water_level > 5 or row.avg_rainfall > 20:
            risk = "medium"
        result.append({
            "latitude": row.latitude,
            "longitude": row.longitude,
            "risk": risk,
            "water_level": row.avg_water_level,
            "rainfall": row.avg_rainfall,
        })

    return result



@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # ✅ Include role in token
    token_data = {"sub": user.username, "role": user.role}
    token = auth.create_access_token(token_data)

    return {"access_token": token, "token_type": "bearer"}

'''