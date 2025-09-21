from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.audit import UserProjectRole
from app.api.v1.auth import get_current_user
from app.db.models.user import User

# Roles base del sistema (podrán ampliarse en sprints futuros)
ROLES = ["admin", "editor", "viewer"]

def _fetch_role(db: Session, user_id: int, project_id: int):
    return db.query(UserProjectRole).filter_by(user_id=user_id, project_id=project_id).first()

def check_role(db: Session, user_id: int, project_id: int, allowed: list[str]):
    r = _fetch_role(db, user_id, project_id)
    if not r or r.role not in allowed:
        raise HTTPException(status_code=403, detail="No permission")
    return True

def require_role(allowed: list[str]):
    def dependency(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
        check_role(db, current_user.id, project_id, allowed)
        return True
    return dependency


def assert_project_access(db: Session, user: User, project_id: int, min_roles: list[str] | None = None):
    """Verifica que el usuario tenga cualquier rol permitido en el proyecto.
    Si min_roles se especifica limita a esos roles, caso contrario cualquier rol existente.
    """
    r = _fetch_role(db, int(user.id), project_id)
    if not r:
        raise HTTPException(status_code=403, detail="No permission")
    if min_roles and r.role not in min_roles:
        raise HTTPException(status_code=403, detail="No permission")
    return True
