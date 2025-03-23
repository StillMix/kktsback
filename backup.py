from fastapi import UploadFile, File
from fastapi.responses import FileResponse
from fastapi import HTTPException, APIRouter, Depends
import os
import shutil

router = APIRouter()

@router.get("/backup/")
async def get_backup():
    file_path = "kkts.db"  
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream', filename='kkts.db')
    else:
        return {"error": "Файл не найден"}


@router.post("/restore/")
async def restore_backup(file: UploadFile = File(...)):
    file_location = "kkts.db"  # Путь для сохранения файла на сервере

    # Сохраняем файл на сервере
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"message": "База данных восстановлена"}