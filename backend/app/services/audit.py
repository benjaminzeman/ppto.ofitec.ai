from sqlalchemy.orm import Session
from app.db.models.audit import AuditLog


def log_action(db: Session, project_id: int, entity: str, entity_id: int, action: str, data: dict, user_id: int | None):
    log = AuditLog(project_id=project_id, entity=entity, entity_id=entity_id, action=action, data=data, user_id=user_id)
    db.add(log)
    db.commit()
