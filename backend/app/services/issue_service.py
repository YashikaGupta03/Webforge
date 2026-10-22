from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from app.models.audit_event import AuditEvent
from app.models.department import Department
from app.models.issue import Issue
from app.models.issue_update import IssueUpdate
from app.models.user import User
from app.schemas.issue import IssueCreate, IssueResponse
from app.services.assignment_service import get_department
from app.services.notification_service import create_notification, notify_roles

DEPARTMENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Electrical": ("electric", "wire", "spark", "light", "fan", "switch", "bijli", "pankha", "current"),
    "Civil and Roads": ("road", "path", "tile", "pothole", "building", "sadak", "gaddha"),
    "Plumbing and Water": ("water", "leak", "tap", "pipe", "drain", "pani", "nal", "seepage"),
    "Sanitation and Housekeeping": ("garbage", "waste", "clean", "dustbin", "kachra", "safai"),
    "Mess and Food": ("mess", "food", "meal", "canteen", "khana"),
    "Hostel and Warden": ("hostel", "warden", "room", "hostel office"),
    "IT and Network": ("wifi", "internet", "network", "computer", "server"),
}
EMERGENCY_KEYWORDS = ("spark", "sparking", "fire", "gas leak", "flood", "injury", "live wire", "aag", "chot")
SAFETY_MESSAGE = "This may be an immediate safety risk. Keep away from the hazard and contact campus emergency services."


def classify_text(text: str) -> tuple[str, float, list[str], bool]:
    normalized = text.casefold()
    matches = {
        department: sum(1 for word in words if word in normalized)
        for department, words in DEPARTMENT_KEYWORDS.items()
    }
    ranked = sorted(matches, key=matches.get, reverse=True)
    best = ranked[0]
    total = sum(matches.values())
    confidence = min(0.95, 0.55 + 0.12 * matches[best]) if matches[best] else 0.35
    if total > 1 and matches[ranked[1]]:
        confidence = min(confidence, matches[best] / total + 0.25)
    if confidence < 0.6:
        best = "Other"
    emergency = any(word in normalized for word in EMERGENCY_KEYWORDS)
    alternatives = [item for item in ranked if matches[item] and item != best][:3]
    if best != "Other":
        alternatives = [best, *alternatives][:3]
    return best, round(confidence, 2), alternatives, emergency


def calculate_priority(text: str, created_at: datetime, related: int = 0) -> dict[str, int | str]:
    normalized = text.casefold()
    safety = 100 if any(word in normalized for word in EMERGENCY_KEYWORDS) else (
        70 if any(word in normalized for word in ("unsafe", "broken", "leak", "slippery")) else 20
    )
    severity = 80 if any(word in normalized for word in ("urgent", "continuous", "broken", "danger", "fire", "flood")) else 45
    impact = 55
    waiting = min(100, int(max(0, (datetime.now(timezone.utc) - created_at).total_seconds() / 3600) / 72 * 100))
    related_score = min(100, related * 10)
    score = round(0.30 * safety + 0.25 * severity + 0.20 * impact + 0.15 * waiting + 0.10 * related_score)
    priority = "Critical" if safety >= 100 or score >= 80 else "High" if score >= 65 else "Medium" if score >= 45 else "Low"
    return {
        "score": score,
        "priority": priority,
        "safety": safety,
        "severity": severity,
        "impact": impact,
        "waiting": waiting,
        "related": related_score,
    }


def next_token(db: Session) -> str:
    now = datetime.now()
    prefix = now.strftime("MNT-%y%m%d%H%M-")
    day_prefix = now.strftime("MNT-%y%m%d")
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:day_prefix))"), {"day_prefix": day_prefix})
    serial = db.scalar(select(func.count()).select_from(Issue).where(Issue.token.like(f"{day_prefix}%")))
    return f"{prefix}{(serial or 0) + 1:04d}"


def issue_to_response(issue: Issue) -> IssueResponse:
    creator = issue.creator.name if issue.creator else "Unknown"
    return IssueResponse(
        id=issue.token,
        title=issue.title,
        description=issue.description,
        category=issue.category,
        location=issue.location,
        priority=issue.priority,
        score=issue.score,
        safety=issue.safety,
        severity=issue.severity,
        impact=issue.impact,
        waiting=issue.waiting,
        related=issue.related,
        confidence=issue.confidence,
        status=issue.status,
        created_at=issue.created_at,
        assigned_to=issue.assigned_to,
        department=issue.department,
        duplicate_of=issue.duplicate_parent.token if issue.duplicate_parent else None,
        updates=[
            {"at": update.created_at.isoformat(), "status": update.status, "note": update.note}
            for update in issue.updates
        ],
        evidence=issue.evidence,
        created_by=creator,
        sla_hours=issue.sla_hours,
    )


def get_issue(db: Session, token: str) -> Issue:
    issue = db.scalar(
        select(Issue)
        .options(
            selectinload(Issue.updates),
            selectinload(Issue.creator),
            selectinload(Issue.duplicate_parent),
        )
        .where(Issue.token == token)
    )
    if issue is None:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return issue


def list_issues(db: Session, user: User) -> list[Issue]:
    query = select(Issue).options(
        selectinload(Issue.updates),
        selectinload(Issue.creator),
        selectinload(Issue.duplicate_parent),
    )
    if user.role == "Student":
        query = query.where(Issue.created_by == user.id)
    elif user.role == "Warden":
        query = query.where(Issue.hostel_id == user.hostel_id)
    elif user.role == "Department Staff":
        query = query.where(Issue.assigned_user_id == user.id)
    return list(db.scalars(query.order_by(Issue.created_at.desc())).unique().all())


def create_issue(db: Session, user: User, data: IssueCreate) -> Issue:
    department_name, confidence, alternatives, emergency = classify_text(
        f"{data.title} {data.description}"
    )
    category = data.category if data.category != "Other" else department_name
    department = get_department(db, category)
    now = datetime.now(timezone.utc)
    priority = calculate_priority(f"{data.title} {data.description}", now)
    issue = Issue(
        id=str(uuid4()),
        token=next_token(db),
        title=data.title.strip(),
        description=data.description.strip(),
        category=category,
        location=data.location.strip(),
        hostel_id=user.hostel_id if user.role == "Student" else (data.hostel_id or user.hostel_id),
        floor=data.floor,
        room=data.room,
        latitude=data.latitude,
        longitude=data.longitude,
        status="Submitted",
        priority=str(priority["priority"]),
        score=int(priority["score"]),
        safety=int(priority["safety"]),
        severity=int(priority["severity"]),
        impact=int(priority["impact"]),
        waiting=int(priority["waiting"]),
        related=int(priority["related"]),
        confidence=confidence,
        priority_breakdown=priority,
        assigned_to="Unassigned",
        department=department.name,
        created_by=user.id,
        sla_hours=department.sla_hours,
        evidence=data.evidence,
    )
    db.add(issue)
    db.flush()
    db.add(IssueUpdate(issue_id=issue.id, status="Submitted", note="Complaint submitted.", actor_id=user.id))
    db.add(AuditEvent(
        issue_id=issue.id,
        actor_id=user.id,
        actor=user.name,
        action="Complaint submitted",
        detail=f"Classification confidence {confidence:.2f}; alternatives: {', '.join(alternatives)}",
        new_value={"category": category, "confidence": confidence, "priority": priority},
    ))
    create_notification(db, user.id, f"Complaint received. Token: {issue.token}", issue.id)
    if emergency:
        notify_roles(db, ("Administrator", "Super Admin"), "Emergency complaint requires immediate review.", issue.id)
    db.commit()
    return get_issue(db, issue.token)


def update_status(db: Session, issue: Issue, user: User, status_value: str, note: str) -> Issue:
    old_status = issue.status
    issue.status = status_value
    if status_value == "Reopened":
        issue.score = min(100, issue.score + 10)
        issue.priority = "Critical" if issue.score >= 80 else "High" if issue.score >= 65 else issue.priority
    db.add(IssueUpdate(issue_id=issue.id, status=status_value, note=note, actor_id=user.id))
    db.add(AuditEvent(
        issue_id=issue.id,
        actor_id=user.id,
        actor=user.name,
        action="Status updated",
        detail=note,
        old_value={"status": old_status},
        new_value={"status": status_value},
    ))
    create_notification(db, issue.created_by, f"Complaint {issue.token}: {status_value}. {note}".strip(), issue.id)
    db.commit()
    return get_issue(db, issue.token)
