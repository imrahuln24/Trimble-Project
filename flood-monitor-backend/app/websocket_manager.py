from typing import List, Any
from fastapi import WebSocket
import json # Keep for potential direct string sending if ever needed.

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.chat_connections: List[WebSocket] = [] # For chat specific broadcasts

    async def connect(self, websocket: WebSocket, connection_type: str = "general"):
        await websocket.accept()
        if connection_type == "chat":
            self.chat_connections.append(websocket)
        else:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, connection_type: str = "general"):
        if connection_type == "chat":
            if websocket in self.chat_connections:
                self.chat_connections.remove(websocket)
        else:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast_general(self, message: dict):
        """Broadcasts to general WebSocket connections (e.g., sensors, alerts)."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to general connection: {e}")
                # Optionally remove problematic connection: self.disconnect(connection, "general")

    async def broadcast_chat(self, message: dict):
        """Broadcasts to chat-specific WebSocket connections."""
        for connection in self.chat_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to chat connection: {e}")
                # Optionally remove problematic connection: self.disconnect(connection, "chat")

    # If you want a single broadcast method that handles types internally:
    # async def broadcast(self, message: dict, target_type: str = "general"):
    #     connections_to_use = self.chat_connections if target_type == "chat" else self.active_connections
    #     for connection in connections_to_use:
    #         await connection.send_json(message)

manager = ConnectionManager() # Global manager instance
'''
from typing import List
from fastapi import WebSocket
from datetime import datetime
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Custom serializer for datetime
        def custom_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {obj.__class__.__name__} not serializable")

        json_message = json.dumps(message, default=custom_serializer)
        for connection in self.active_connections:
            await connection.send_json(json_message)

'''