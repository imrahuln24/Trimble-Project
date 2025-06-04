# app/routers/chat_router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query # Added Query
from sqlalchemy.orm import Session
from typing import List
import json
import pydantic

from app import crud, models, schemas, auth, database # Import database directly for SessionLocal
from app.websocket_manager import manager as connection_manager

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.websocket("/ws")
async def websocket_chat_endpoint_route( # Renamed
    websocket: WebSocket,
    token: str = Query(...) # Get token from query parameter
    # db: Session = Depends(get_db) # Cannot use Depends for DB directly like this in WS
):
    db: Session = database.SessionLocal() # Create a new session for this WebSocket connection
    try:
        # Manually call get_current_user with the token from query and the new db session
        current_user = await auth.get_current_user(token=token, db=db)
        print(f"User {current_user.username} authenticated for chat WebSocket.")
    except HTTPException as e:
        print(f"Chat WebSocket authentication failed: {e.detail}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        db.close()
        return
    except Exception as e: # Catch any other auth errors
        print(f"Chat WebSocket generic authentication error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        db.close()
        return

    await connection_manager.connect(websocket, connection_type="chat")
    print(f"User {current_user.username} connected to chat.")
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
                message_data = schemas.MessageCreate(**payload)
            except (json.JSONDecodeError, pydantic.ValidationError) as e:
                error_detail = e.errors() if isinstance(e, pydantic.ValidationError) else str(e)
                await websocket.send_text(json.dumps({"error": "Invalid message format/structure.", "details": error_detail}))
                continue
            
            db_message = crud.create_message(db, message=message_data, user_id=current_user.id)
            chat_message_out = schemas.MessageOut.model_validate(db_message)
            await connection_manager.broadcast_chat(
                {"type": "new_message", "data": chat_message_out.model_dump(mode='json')}
            )
    except WebSocketDisconnect:
        print(f"User {current_user.username} disconnected from chat.")
    except Exception as e:
        print(f"Chat WebSocket error for user {current_user.username}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        connection_manager.disconnect(websocket, connection_type="chat")
        db.close() # Crucial to close the session
        print(f"Chat WebSocket connection closed for {current_user.username}.")


@router.get("/messages", response_model=List[schemas.MessageOut])
async def get_historical_chat_messages_route( # Renamed
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    messages_orm = crud.get_messages(db, skip=skip, limit=limit)
    return messages_orm # FastAPI handles conversion


'''
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json # For parsing incoming WebSocket message
import pydantic # For validation error handling

from app import crud, models, schemas, auth
from app.database import get_db
# Use the global manager instance from websocket_manager
from app.websocket_manager import manager as connection_manager

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.websocket("/ws")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str = Depends(auth.oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        current_user = await auth.get_current_user(token=token, db=db)
        print(f"User {current_user.username} connected to chat.") # Log connection
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(websocket, connection_type="chat")
    try:
        while True:
            raw_data = await websocket.receive_text() # Data is a JSON string
            try:
                payload = json.loads(raw_data)
                # Validate incoming data against MessageCreate schema (expects "content" field)
                message_data = schemas.MessageCreate(**payload)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"error": "Invalid JSON format."}))
                continue
            except pydantic.ValidationError as e:
                await websocket.send_text(json.dumps({"error": "Invalid message structure.", "details": e.errors()}))
                continue
            except Exception as e: # Catch any other parsing/validation errors
                await websocket.send_text(json.dumps({"error": f"Cannot process message: {str(e)}"}))
                continue

            # Store message in DB (create_message expects MessageCreate and user_id)
            # crud.create_message now returns the Message ORM object with user eagerly loaded
            db_message = crud.create_message(db, message=message_data, user_id=current_user.id)

            # Prepare for broadcast using MessageOut schema for proper serialization (including username)
            # .model_validate replaces .from_orm in Pydantic V2
            chat_message_out = schemas.MessageOut.model_validate(db_message)

            # Broadcast to all chat clients. model_dump(mode='json') ensures datetime is ISO string.
            await connection_manager.broadcast_chat(
                {"type": "new_message", "data": chat_message_out.model_dump(mode='json')}
            )
    except WebSocketDisconnect:
        print(f"User {current_user.username} disconnected from chat.") # Log disconnection
        connection_manager.disconnect(websocket, connection_type="chat")
    except Exception as e:
        print(f"Chat WebSocket error for user {current_user.username}: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        connection_manager.disconnect(websocket, connection_type="chat")
        # Don't try to close if already closed by WebSocketDisconnect
        if websocket.client_state != websocket.client_state.DISCONNECTED:
             await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.get("/messages", response_model=List[schemas.MessageOut])
async def get_historical_chat_messages(
    skip: int = 0, # Added skip parameter for consistency
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    messages_orm = crud.get_messages(db, skip=skip, limit=limit)
    # FastAPI will automatically convert using MessageOut.model_validate (from_attributes)
    # Ensure crud.get_messages eagerly loads user for MessageOut.username
    return messages_orm

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import crud, models, schemas, auth
from app.database import get_db
from app.websocket_manager import chat_manager # Use dedicated chat manager

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.websocket("/ws")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str = Depends(auth.oauth2_scheme), # Require auth for chat WS
    db: Session = Depends(get_db) # Need db if we store messages via WS too
):
    try:
        current_user = await auth.get_current_user(token=token, db=db) # Authenticate user for WS
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await chat_manager.connect(websocket, connection_type="chat")
    try:
        while True:
            data = await websocket.receive_text()
            # Minimal processing: assume data is a JSON string with a "message" field
            try:
                message_data = schemas.ChatMessageCreate(message=data) # Or parse JSON if more complex
            except Exception: # Handle malformed message
                await websocket.send_text("Error: Invalid message format.")
                continue

            # Store message in DB
            db_message = crud.create_chat_message(db, message=message_data, user_id=current_user.id, username=current_user.username)
            
            # Broadcast to all chat clients
            chat_message_out = schemas.ChatMessageOut.from_orm(db_message)
            await chat_manager.broadcast(
                {"type": "new_message", "data": chat_message_out.model_dump()},
                connection_type="chat"
            )
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket, connection_type="chat")
    except Exception as e:
        print(f"Chat WebSocket error: {e}")
        chat_manager.disconnect(websocket, connection_type="chat")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.get("/messages", response_model=List[schemas.ChatMessageOut])
async def get_historical_chat_messages(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user) # Auth
):
    messages = crud.get_chat_messages(db, limit=limit)
    return messages
'''