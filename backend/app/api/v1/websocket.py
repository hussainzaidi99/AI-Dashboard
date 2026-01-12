"""
WebSocket API Endpoints
Real-time communication for processing status and notifications
"""
#backend/app/api/v1/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import logging

from app.config import settings
from app.models.mongodb_models import ProcessingJob, FileUpload

router = APIRouter()
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, file_id: str):
        """Connect a WebSocket client"""
        await websocket.accept()
        
        if file_id not in self.active_connections:
            self.active_connections[file_id] = set()
        
        self.active_connections[file_id].add(websocket)
        logger.info(f"WebSocket connected for file: {file_id}")
    
    def disconnect(self, websocket: WebSocket, file_id: str):
        """Disconnect a WebSocket client"""
        if file_id in self.active_connections:
            self.active_connections[file_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[file_id]:
                del self.active_connections[file_id]
        
        logger.info(f"WebSocket disconnected for file: {file_id}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to a specific client"""
        await websocket.send_json(message)
    
    async def broadcast_to_file(self, message: dict, file_id: str):
        """Broadcast message to all clients watching a file"""
        if file_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[file_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Remove disconnected clients
            for connection in disconnected:
                self.disconnect(connection, file_id)
    
    async def broadcast_all(self, message: dict):
        """Broadcast message to all connected clients"""
        for file_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/status/{file_id}")
async def websocket_status(websocket: WebSocket, file_id: str):
    """
    WebSocket endpoint for real-time processing status updates
    
    Clients can connect to receive updates about file processing progress
    """
    if not settings.ENABLE_WEBSOCKET:
        await websocket.close(code=1008, reason="WebSocket disabled")
        return
    
    await manager.connect(websocket, file_id)
    
    try:
        # Send initial status
        # Retrieve status from MongoDB
        job = await ProcessingJob.find_one(ProcessingJob.file_id == file_id)
        if job:
            status_data = {
                "file_id": file_id,
                "status": job.status,
                "progress": job.progress,
                "error": job.error_message
            }
        else:
            # Check if file exists but no job yet
            file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
            if file_upload:
                status_data = {
                    "file_id": file_id,
                    "status": "uploaded",
                    "progress": 0
                }
            else:
                status_data = None

        if status_data:
            await manager.send_personal_message(
                {
                    "type": "status_update",
                    "file_id": file_id,
                    "data": status_data
                },
                websocket
            )
        else:
            await manager.send_personal_message(
                {
                    "type": "error",
                    "message": "File not found"
                },
                websocket
            )
        
        # Listen for messages from client
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get('type') == 'ping':
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": message.get('timestamp')},
                    websocket
                )
            
            elif message.get('type') == 'get_status':
                # Retrieve status from MongoDB
                job = await ProcessingJob.find_one(ProcessingJob.file_id == file_id)
                status_data = None
                
                if job:
                    status_data = {
                        "file_id": file_id,
                        "status": job.status,
                        "progress": job.progress,
                        "error": job.error_message
                    }
                else:
                    file_upload = await FileUpload.find_one(FileUpload.file_id == file_id)
                    if file_upload:
                        status_data = {
                            "file_id": file_id,
                            "status": "uploaded",
                            "progress": 0
                        }

                if status_data:
                    await manager.send_personal_message(
                        {
                            "type": "status_update",
                            "file_id": file_id,
                            "data": status_data
                        },
                        websocket
                    )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, file_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket, file_id)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """
    WebSocket endpoint for general notifications
    
    Receives notifications about system events, new insights, etc.
    """
    if not settings.ENABLE_WEBSOCKET:
        await websocket.close(code=1008, reason="WebSocket disabled")
        return
    
    await websocket.accept()
    connection_id = id(websocket)
    logger.info(f"Notification WebSocket connected: {connection_id}")
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to notifications stream"
        })
        
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get('type') == 'ping':
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": message.get('timestamp')
                })
    
    except WebSocketDisconnect:
        logger.info(f"Notification WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Notification WebSocket error: {str(e)}")


# Helper function to broadcast status updates
async def broadcast_status_update(file_id: str, status_data: dict):
    """
    Broadcast status update to all clients watching a file
    
    This should be called from other parts of the application
    when processing status changes
    """
    await manager.broadcast_to_file(
        {
            "type": "status_update",
            "file_id": file_id,
            "data": status_data
        },
        file_id
    )


# Helper function to broadcast notifications
async def broadcast_notification(notification: dict):
    """
    Broadcast a notification to all connected clients
    """
    await manager.broadcast_all({
        "type": "notification",
        "data": notification
    })