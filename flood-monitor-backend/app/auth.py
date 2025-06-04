from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import models, schemas, crud, database
# Import utilities from the new security.py
from .security import verify_password, SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login") # tokenUrl points to the login endpoint in main.py

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = crud.get_user(db, username=username) # Depends on crud.py
    if not user:
        return None
    if not verify_password(password, user.hashed_password): # Uses verify_password from security.py
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # Uses SECRET_KEY, ALGORITHM from security.py
        username: Optional[str] = payload.get("sub")
        role_str: Optional[str] = payload.get("role")

        if username is None or role_str is None:
            raise credentials_exception
        
        try:
            # Validate role string against Pydantic Enum
            token_data = schemas.TokenData(username=username, role=schemas.RoleEnum(role_str))
        except ValueError: # Invalid role string
             raise credentials_exception
             
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user(db, username=token_data.username) # type: ignore # Depends on crud.py
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    # Example: if you add a 'disabled' field to User model
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def role_checker(allowed_roles: List[schemas.RoleEnum]):
    async def checker(current_user: models.User = Depends(get_current_active_user)):
        # Ensure comparison is between same types or their string values
        current_user_role_enum_value = current_user.role.value # Get string value from SQLAlchemy Enum
        
        # Convert allowed_roles (Pydantic Enums) to their string values for comparison
        allowed_role_values = [role.value for role in allowed_roles]

        if current_user_role_enum_value not in allowed_role_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. User role '{current_user_role_enum_value}' not in allowed roles: {allowed_role_values}",
            )
        return current_user
    return checker


'''from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from . import models, schemas, crud, database # Ensure crud is imported if get_user is used

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key") # USE A STRONG KEY FROM ENV VAR
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 # 30 days for easier dev, reduce for prod

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login") # Corrected tokenUrl

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = crud.get_user(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role") # Role is stored as string in token
        if username is None or role is None:
            raise credentials_exception
        # Ensure the role from token is valid against our Enum
        try:
            token_data = schemas.TokenData(username=username, role=schemas.RoleEnum(role))
        except ValueError: # Invalid role string
             raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    # if current_user.disabled: # If you add a 'disabled' field to User model
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Dependency for role-based access control
def role_checker(allowed_roles: list[schemas.RoleEnum]):
    async def checker(current_user: models.User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this user role",
            )
        return current_user
    return checker'''
