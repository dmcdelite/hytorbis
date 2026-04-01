from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from datetime import datetime, timezone
import random


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.user_info: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, world_id: str, user_id: str):
        await websocket.accept()
        if world_id not in self.active_connections:
            self.active_connections[world_id] = []
        self.active_connections[world_id].append(websocket)
        self.user_info[f"{world_id}:{user_id}"] = {
            "websocket": websocket,
            "cursor": {"x": 0, "y": 0},
            "color": f"#{random.randint(0, 0xFFFFFF):06x}",
            "joined_at": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(world_id, {
            "type": "user_joined",
            "user_id": user_id,
            "users": self.get_users(world_id)
        }, exclude=websocket)

    def disconnect(self, websocket: WebSocket, world_id: str, user_id: str):
        if world_id in self.active_connections:
            if websocket in self.active_connections[world_id]:
                self.active_connections[world_id].remove(websocket)
        key = f"{world_id}:{user_id}"
        if key in self.user_info:
            del self.user_info[key]

    def get_users(self, world_id: str) -> List[Dict]:
        users = []
        for key, info in self.user_info.items():
            if key.startswith(f"{world_id}:"):
                user_id = key.split(":")[1]
                users.append({
                    "user_id": user_id,
                    "cursor": info["cursor"],
                    "color": info["color"]
                })
        return users

    async def broadcast(self, world_id: str, message: dict, exclude: WebSocket = None):
        if world_id in self.active_connections:
            for connection in self.active_connections[world_id]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        pass

    async def update_cursor(self, world_id: str, user_id: str, x: int, y: int):
        key = f"{world_id}:{user_id}"
        if key in self.user_info:
            self.user_info[key]["cursor"] = {"x": x, "y": y}


ws_manager = ConnectionManager()
