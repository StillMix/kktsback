from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

# websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()

# Список активных подключений
active_connections: List[WebSocket] = []

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Принятие подключения
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Получаем сообщение от клиента
            message = await websocket.receive_text()
            # Рассылаем сообщение всем подключённым клиентам
            for connection in active_connections:
                if connection != websocket:
                    await connection.send_text(f"New message: {message}")
    except WebSocketDisconnect:
        # Если клиент отключается, убираем его из списка активных подключений
        active_connections.remove(websocket)
