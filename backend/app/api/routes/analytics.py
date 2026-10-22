from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.issue import Issue
from app.models.user import User

router = APIRouter()


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("Administrator", "Super Admin")),
) -> dict[str, object]:
    total = db.scalar(select(func.count()).select_from(Issue)) or 0
    resolved = db.scalar(select(func.count()).select_from(Issue).where(Issue.status == "Resolved")) or 0
    by_category = db.execute(
        select(Issue.category, func.count(Issue.id)).group_by(Issue.category)
    ).all()
    by_status = db.execute(
        select(Issue.status, func.count(Issue.id)).group_by(Issue.status)
    ).all()
    return {
        "total": total,
        "resolved": resolved,
        "open": total - resolved,
        "by_category": {category: count for category, count in by_category},
        "by_status": {status: count for status, count in by_status},
    }
