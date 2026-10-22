from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.user import User
from app.services.notification_service import create_notification
from app.models.audit_event import AuditEvent
from app.models.issue import Issue
from app.models.issue_update import IssueUpdate


def get_department(db: Session, name: str) -> Department:
    department = db.scalar(select(Department).where(Department.name == name))
    if department is None:
        raise HTTPException(status_code=422, detail="Unknown department.")
    return department


def get_assignable_staff(db: Session, department_id: int) -> list[User]:
    return list(db.scalars(
        select(User)
        .where(
            User.role == "Department Staff",
            User.department_id == department_id,
            User.is_active.is_(True),
        )
        .order_by(User.name)
    ).all())


def assign_issue(
    db: Session,
    issue: Issue,
    actor: User,
    department_name: str,
    staff_name: str,
) -> Issue:
    department = get_department(db, department_name)
    staff = db.scalar(
        select(User).where(
            User.name == staff_name,
            User.role == "Department Staff",
            User.department_id == department.id,
            User.is_active.is_(True),
        )
    )
    if staff is None:
        raise HTTPException(status_code=422, detail="Select an active staff member in this department.")

    old_department, old_assignee, old_status = issue.department, issue.assigned_to, issue.status
    issue.department = department.name
    issue.assigned_to = staff.name
    issue.assigned_user_id = staff.id
    issue.status = "Assigned"
    note = f"Assigned to {staff.name} ({department.name})."
    db.add(IssueUpdate(issue_id=issue.id, status="Assigned", note=note, actor_id=actor.id))
    db.add(AuditEvent(
        issue_id=issue.id,
        actor_id=actor.id,
        actor=actor.name,
        action="Issue assigned",
        detail=note,
        old_value={"department": old_department, "assignedTo": old_assignee, "status": old_status},
        new_value={"department": department.name, "assignedTo": staff.name, "status": "Assigned"},
    ))
    create_notification(db, issue.created_by, note, issue.id)
    db.commit()
    return issue
