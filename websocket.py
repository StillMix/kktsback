from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()

# Словарь активных подключений {user_id: WebSocket}
active_connections: Dict[int, WebSocket] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Подключение WebSocket с передачей user_id"""
    await websocket.accept()
    active_connections[user_id] = websocket  # Запоминаем подключение
    
    try:
        while True:
            message = await websocket.receive_text()
            # Рассылаем сообщение всем (если нужно)
            for uid, connection in active_connections.items():
                if uid != user_id:  # Исключаем отправителя
                    await connection.send_text(f"New message: {message}")
    except WebSocketDisconnect:
        # Если клиент отключается, убираем его из списка
        if user_id in active_connections:
            del active_connections[user_id]

async def notify_disconnect_user(user_id: int, user_name: str, role: str):
    """Отключает пользователя по его ID и имени"""
    connection = active_connections.get((user_id, user_name))
    if connection:
        try:
            # Отправляем сообщение об отключении с ID, именем и ролью
            await connection.send_text(f"logout:{user_id},{user_name},{role}")
        except Exception as e:
            pass  # Ошибку можно залогировать
        finally:
            # Убираем пользователя из списка активных подключений
            del active_connections[(user_id, user_name)]  # Используем кортеж (id, name) как ключ
