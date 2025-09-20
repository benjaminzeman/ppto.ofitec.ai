import os, json, uuid, tempfile, traceback
from datetime import datetime
from typing import Callable, Any
from rq import Queue
from redis import Redis
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.job import Job

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def _redis_conn():
    return Redis.from_url(REDIS_URL)

def get_queue(name: str = "default") -> Queue:
    return Queue(name, connection=_redis_conn())

def enqueue_job(db: Session, job_type: str, func: Callable, **kwargs) -> Job:
    q = get_queue()
    rq_job = q.enqueue(call_wrapped, func_path=f"{func.__module__}:{func.__name__}", job_type=job_type, kwargs=kwargs)
    job = Job(rq_id=rq_job.id, type=job_type, status="queued", params=json.dumps(kwargs))
    db.add(job); db.commit(); db.refresh(job)
    return job

def call_wrapped(func_path: str, job_type: str, kwargs: dict):
    """Wrapper ejecutado en el worker RQ. Maneja DB y actualización de estado."""
    module_name, fn_name = func_path.split(":")
    from importlib import import_module
    module = import_module(module_name)
    fn = getattr(module, fn_name)
    db: Session = SessionLocal()
    job_record: Job | None = None
    try:
        # localizar registro
        from rq import get_current_job
        current = get_current_job()
        job_record = db.query(Job).filter_by(rq_id=current.id).first()
        if job_record:
            job_record.status = "started"; job_record.updated_at = datetime.utcnow(); db.commit()
        result = fn(db=db, **kwargs)
        result_path = None
        # Si el resultado es bytes => lo escribimos a un archivo temporal
        if isinstance(result, (bytes, bytearray)):
            fd, path = tempfile.mkstemp(prefix=f"job_{job_type}_", suffix=".bin")
            with os.fdopen(fd, "wb") as f:
                f.write(result)
            result_path = path
        elif isinstance(result, str) and os.path.exists(result):
            result_path = result
        if job_record:
            job_record.status = "finished"
            job_record.result_path = result_path
            job_record.updated_at = datetime.utcnow()
            db.commit()
    except Exception as e:  # pragma: no cover - logging simple
        if job_record:
            job_record.status = "failed"
            job_record.error = f"{e}\n{traceback.format_exc()}"
            job_record.updated_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()

def get_job_status(db: Session, job_id: int) -> Job | None:
    return db.get(Job, job_id)
