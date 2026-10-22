from sqlalchemy.orm import Session
from typing import Optional

from app.models.notification import Notification


def create_notification(
    db: Session,
    user_id: str,
    text: str,
    issue_id: Optional[str] = None,
) -> Notification:
    notification = Notification(user_id=user_id, text=text, issue_id=issue_id, is_read=False)
    db.add(notification)
    return notification


def notify_roles(
    db: Session,
    roles: tuple[str, ...],
    text: str,
    issue_id: Optional[str] = None,
) -> None:
    from sqlalchemy import select

    from app.models.user import User

    recipients = db.scalars(select(User).where(User.role.in_(roles), User.is_active.is_(True))).all()
    for recipient in recipients:
        create_notification(db, recipient.id, text, issue_id)
