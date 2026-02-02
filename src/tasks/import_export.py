from celery import Task
from typing import Optional
from src.celery_app import celery_app
from src.database import AsyncSessionLocal
from src.repositories.batch import BatchRepository
from src.repositories.work_center import WorkCenterRepository
from src.services.minio_service import minio_service
from src.schemas.batch import BatchCreate
import tempfile
import os


@celery_app.task(bind=True, max_retries=1)
def import_batches_from_file(
    self: Task,
    file_url: str,
    user_id: int
) -> dict:
    """
    Импорт партий из Excel/CSV файла.
    
    Args:
        file_url: URL файла в MinIO
        user_id: ID пользователя для отправки результата
    
    Returns:
        {
            "success": True,
            "total_rows": 100,
            "created": 95,
            "skipped": 5,
            "errors": [...]
        }
    """
    import asyncio
    import pandas as pd
    
    async def _import():
        async with AsyncSessionLocal() as session:
            await session.begin()
            try:
                # Download file from MinIO
                # Extract bucket and object_name from URL
                # For simplicity, assume file_url contains bucket/object_name
                # In production, parse the URL properly
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                temp_file.close()
                
                # Download (simplified - in production parse URL properly)
                # minio_service.download_file("imports", object_name, temp_file.name)
                
                # For now, assume file is already downloaded
                # Read Excel file
                df = pd.read_excel(temp_file.name)
                
                total_rows = len(df)
                created = 0
                skipped = 0
                errors = []
                
                batch_repo = BatchRepository(session)
                work_center_repo = WorkCenterRepository(session)
                
                for idx, row in df.iterrows():
                    try:
                        # Get or create work center
                        work_center = await work_center_repo.get_or_create(
                            identifier=row.get("ИдентификаторРЦ", ""),
                            name=row.get("РабочийЦентр", "")
                        )
                        
                        # Create batch
                        batch_data = BatchCreate(
                            is_closed=row.get("СтатусЗакрытия", False),
                            task_description=row.get("ПредставлениеЗаданияНаСмену", ""),
                            work_center_id=work_center.id,
                            shift=row.get("Смена", ""),
                            team=row.get("Бригада", ""),
                            batch_number=int(row.get("НомерПартии", 0)),
                            batch_date=pd.to_datetime(row.get("ДатаПартии")).date(),
                            nomenclature=row.get("Номенклатура", ""),
                            ekn_code=row.get("КодЕКН", ""),
                            shift_start=pd.to_datetime(row.get("ДатаВремяНачалаСмены")),
                            shift_end=pd.to_datetime(row.get("ДатаВремяОкончанияСмены")),
                        )
                        
                        await batch_repo.create(batch_data)
                        created += 1
                        
                        # Update progress
                        self.update_state(
                            state="PROGRESS",
                            meta={
                                "current": idx + 1,
                                "total": total_rows,
                                "created": created,
                                "skipped": skipped
                            }
                        )
                        
                    except Exception as e:
                        skipped += 1
                        errors.append({
                            "row": idx + 1,
                            "error": str(e)
                        })
                
                await session.commit()
                os.remove(temp_file.name)
                
                return {
                    "success": True,
                    "total_rows": total_rows,
                    "created": created,
                    "skipped": skipped,
                    "errors": errors
                }
                
            except Exception as e:
                await session.rollback()
                raise e
    
    try:
        result = asyncio.run(_import())
        return result
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task
def export_batches_to_file(
    filters: dict,
    format: str = "excel"
) -> dict:
    """
    Экспорт списка партий в файл.
    
    Args:
        filters: Фильтры для выборки партий
        format: "excel" или "csv"
    
    Returns:
        {
            "success": True,
            "file_url": "...",
            "total_batches": 150
        }
    """
    import asyncio
    import pandas as pd
    
    async def _export():
        async with AsyncSessionLocal() as session:
            batch_repo = BatchRepository(session)
            
            batches, total = await batch_repo.list(
                is_closed=filters.get("is_closed"),
                batch_date=filters.get("batch_date"),
                work_center_id=filters.get("work_center_id"),
                shift=filters.get("shift"),
                offset=0,
                limit=10000  # Large limit for export
            )
            
            # Convert to DataFrame
            data = []
            for batch in batches:
                data.append({
                    "НомерПартии": batch.batch_number,
                    "ДатаПартии": str(batch.batch_date),
                    "Статус": "Закрыта" if batch.is_closed else "Открыта",
                    "РабочийЦентр": batch.work_center.name if batch.work_center else "",
                    "Смена": batch.shift,
                    "Бригада": batch.team,
                    "Номенклатура": batch.nomenclature,
                    "КодЕКН": batch.ekn_code,
                })
            
            df = pd.DataFrame(data)
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
            temp_file.close()
            
            if format == "excel":
                df.to_excel(temp_file.name, index=False)
            else:
                df.to_csv(temp_file.name, index=False)
            
            # Upload to MinIO
            from datetime import datetime
            file_name = f"batches_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format}"
            file_url = minio_service.upload_file(
                bucket="exports",
                file_path=temp_file.name,
                object_name=file_name,
                expires_days=7
            )
            
            os.remove(temp_file.name)
            
            return {
                "success": True,
                "file_url": file_url,
                "total_batches": total
            }
    
    return asyncio.run(_export())
