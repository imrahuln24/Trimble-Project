# app/schemas.py
from pydantic import BaseModel, Field, field_serializer, computed_field
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

# --- Pydantic V2 Style Config ---
# Common config to be reused if needed, or apply directly
PYDANTIC_V2_MODEL_CONFIG = {
    "from_attributes": True, # Replaces orm_mode = True
}

class SensorDataCreate(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    water_level: float
    rainfall: float

class SensorDataOut(BaseModel):
    id: int
    sensor_id: str
    latitude: float
    longitude: float
    water_level: float
    rainfall: float
    timestamp: datetime

    model_config = PYDANTIC_V2_MODEL_CONFIG

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        return dt.isoformat()


class RoleEnum(str, PyEnum):
    admin = "admin"
    field_responder = "field_responder"
    commander = "commander"
    government_official = "government_official"
    viewer = "viewer"

class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum

class UserOut(BaseModel):
    id: int
    username: str
    role: RoleEnum

    model_config = PYDANTIC_V2_MODEL_CONFIG

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[RoleEnum] = None


class AlertCreate(BaseModel):
    title: str
    description: str
    level: str # e.g. info, warning, critical
    sensor_id: Optional[str] = None

class AlertOut(AlertCreate):
    id: int
    timestamp: datetime
    is_resolved: bool

    model_config = PYDANTIC_V2_MODEL_CONFIG

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        return dt.isoformat()

# Schemas for Chat
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase): # Used for incoming WebSocket message content
    pass

class MessageOut(MessageBase): # Used for broadcasting and fetching messages
    id: int
    user_id: int
    # username: str # Will be a computed field
    timestamp: datetime

    @computed_field
    @property
    def username(self) -> str:
        # This assumes 'self' is the ORM model instance (models.Message)
        # when model_validate (from_attributes=True) is called.
        # Ensure 'user' relationship is loaded on the ORM model.
        if hasattr(self, 'user') and self.user: # Check if user attribute exists and is not None
            return self.user.username
        return "Unknown User" # Fallback or raise error

    model_config = PYDANTIC_V2_MODEL_CONFIG

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        return dt.isoformat()


class RiskPoint(BaseModel):
    latitude: float
    longitude: float
    risk_level: str
    water_level: Optional[float] = None
    sensor_id: Optional[str] = None
    last_updated: Optional[datetime] = None

    model_config = PYDANTIC_V2_MODEL_CONFIG

    @field_serializer('last_updated')
    def serialize_last_updated(self, dt: Optional[datetime], _info):
        return dt.isoformat() if dt else None

# For spatial_router.py /sensors-in-radius endpoint
# Assumed it should return more than just location, perhaps SensorDataOut or a subset
# If it was schemas.SensorLocation, define it:
class SensorLocation(BaseModel): # Example, adjust fields as needed
    id: int
    sensor_id: str
    latitude: float
    longitude: float
    water_level: Optional[float] = None
    rainfall: Optional[float] = None
    timestamp: datetime

    model_config = PYDANTIC_V2_MODEL_CONFIG

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        return dt.isoformat()

class SpatialQueryCircle(BaseModel):
    latitude: float
    longitude: float
    radius_km: float
    # min_water_level: Optional[float] = None # this was in mapService.js, add if needed for POST body
    
'''
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum as PyEnum # Rename to avoid conflict with models.RoleEnum
from typing import Optional

# Keep your existing SensorDataCreate and SensorDataOut as they are
class SensorDataCreate(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    water_level: float
    rainfall: float

class SensorDataOut(BaseModel):
    id: int
    sensor_id: str
    latitude: float
    longitude: float
    water_level: float
    rainfall: float
    timestamp: datetime

    class Config:
        from_attributes = True


# Updated RoleEnum to match models.py
class RoleEnum(str, PyEnum):
    admin = "admin"
    field_responder = "field_responder"
    commander = "commander"
    government_official = "government_official"
    viewer = "viewer"

class UserCreate(BaseModel):
    username: str
    password: str
    role: RoleEnum # Use the Pydantic Enum

class UserOut(BaseModel):
    id: int
    username: str
    role: RoleEnum

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[RoleEnum] = None


class AlertCreate(BaseModel):
    title: str
    description: str
    level: str
    sensor_id: Optional[str] = None

class AlertOut(AlertCreate):
    id: int
    timestamp: datetime
    is_resolved: bool

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Schemas for Chat
class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessageOut(MessageBase):
    id: int
    user_id: int
    username: str # To display sender's name
    timestamp: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RiskPoint(BaseModel):
    latitude: float
    longitude: float
    risk_level: str # e.g., "low", "medium", "high"
    water_level: Optional[float] = None
    sensor_id: Optional[str] = None
    last_updated: Optional[datetime] = None

from pydantic import BaseModel
from datetime import datetime

class SensorDataCreate(BaseModel):
    sensor_id: str
    latitude: float
    longitude: float
    water_level: float
    rainfall: float

from pydantic import BaseModel
from datetime import datetime

class SensorDataOut(BaseModel):
    id: int
    sensor_id: str
    latitude: float
    longitude: float
    water_level: float
    rainfall: float
    timestamp: datetime

    class Config:
        from_attributes = True

from pydantic import BaseModel
from enum import Enum

class RoleEnum(str, Enum): #field commander official
    admin = "admin"
    responder = "responder"
    viewer = "viewer"

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
   # role: RoleEnum = RoleEnum.viewer


class UserOut(BaseModel):
    id: int
    username: str
    role: RoleEnum

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    
class AlertCreate(BaseModel):
    title: str
    description: str
    level: str

class AlertOut(AlertCreate):
    id: int
    timestamp: datetime
    is_resolved: bool

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()  # <- Fixes your error
        }
'''