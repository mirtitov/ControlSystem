from celery.result import AsyncResult
from fastapi import APIRouter

from src.celery_app import celery_app

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """Получение статуса задачи"""
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == "PENDING":
        response = {"task_id": task_id, "status": "PENDING", "result": None}
    elif task_result.state == "PROGRESS":
        response = {
            "task_id": task_id,
            "status": "PROGRESS",
            "result": task_result.info,
        }
    elif task_result.state == "SUCCESS":
        response = {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task_result.result,
        }
    else:  # FAILURE
        response = {
            "task_id": task_id,
            "status": "FAILURE",
            "result": {"error": str(task_result.info)},
        }

    return response
