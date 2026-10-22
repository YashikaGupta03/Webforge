from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.user import User

router = APIRouter()


@router.get("")
def audit_events(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("Administrator", "Super Admin")),
) -> list[dict[str, object]]:
    events = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc())).all()
    return [
        {
            "id": event.id,
            "at": event.created_at.isoformat(),
            "actor": event.actor,
            "action": event.action,
            "issueId": event.issue_id,
            "detail": event.detail,
        }
        for event in events
    ]
