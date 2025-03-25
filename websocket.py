from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict,List

router = APIRouter()

# Словарь активных подключений {user_id: WebSocket}
active_connections: Dict[int, WebSocket] = {}
active_group_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """Подключение WebSocket с передачей user_id"""
    await websocket.accept()
    active_connections[user_id] = websocket  # Запоминаем подключение

    group = "group1"  # Пример группы
    if group not in active_group_connections:
        active_group_connections[group] = []
    
    active_group_connections[group].append(websocket)
    print(f"User {user_id} connected to group {group}")  # Логируем подключение

    # Отправляем сообщение сразу после подключения
    try:
        await websocket.send_text("Hello from server")  # Отправляем приветственное сообщение клиенту
    except Exception as e:
        print(f"Error sending message to client: {e}")

    try:
        while True:
            message = await websocket.receive_text()
            print(f"Message received: {message}")  # Логируем получение сообщения
            
            # Убедимся, что сообщение отправляется по всей группе
            if group in active_group_connections:
                print(f"Sending message to group {group}")  # Логируем рассылку
                for connection in active_group_connections[group]:
                    if connection != websocket:
                        try:
                            await connection.send_text(f"New message: {message}")
                            print(f"Message sent to connection: {connection}")  # Логируем отправку
                        except Exception as e:
                            print(f"Error sending message to connection: {e}")
    except WebSocketDisconnect:
        # Если клиент отключается, убираем его из списка
        if user_id in active_connections:
            del active_connections[user_id]
            print(f"User {user_id} disconnected")



async def notify_racp_group(group: str, message: str):
    """Выдаем обновившееся расписание всем пользователям, независимо от группы"""
    # Перебираем все активные соединения и отправляем им сообщение
    for connection in active_connections.values():
        try:
            await connection.send_text(message)
        except Exception as e:
            print(f"Error sending message to a user: {e}")



async def notify_disconnect_user(user_id: int, user_name: str, role: str):
    """Отключает пользователя по его ID и имени"""
    connection = active_connections.get(user_id)  # Получаем соединение по user_id
    if connection:
        try:
            # Отправляем сообщение об отключении с ID, именем и ролью
            await connection.send_text(f"logout:{user_id},{user_name},{role}")
        except Exception as e:
            pass  # Ошибку можно залогировать
        finally:
            # Убираем пользователя из списка активных подключений
            del active_connections[user_id] 