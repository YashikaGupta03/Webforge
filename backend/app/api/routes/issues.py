from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.issue import Issue
from app.models.user import User
from app.schemas.issue import (
    AssignmentRequest,
    DuplicateLinkRequest,
    IssueChatRequest,
    IssueChatResponse,
    IssueCreate,
    IssueResponse,
    IssueUpdateRequest,
)
from app.services.assignment_service import assign_issue
from app.services.issue_service import (
    SAFETY_MESSAGE,
    classify_text,
    create_issue,
    get_issue,
    issue_to_response,
    list_issues,
    update_status,
)
from app.services.notification_service import notify_roles

router = APIRouter()


def ensure_issue_access(issue: Issue, user: User) -> None:
    if user.role == "Student" and issue.created_by != user.id:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if user.role == "Warden" and user.hostel_id != issue.hostel_id:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if user.role == "Department Staff" and issue.assigned_user_id != user.id:
        raise HTTPException(status_code=404, detail="Complaint not found.")


@router.get("", response_model=list[IssueResponse])
def get_issues(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[IssueResponse]:
    return [issue_to_response(issue) for issue in list_issues(db, user)]


@router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def post_issue(
    data: IssueCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Student", "Administrator", "Super Admin", "Warden")),
) -> IssueResponse:
    return issue_to_response(create_issue(db, user, data))


@router.post("/chat", response_model=IssueChatResponse)
def chat(
    data: IssueChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Student")),
) -> IssueChatResponse:
    message = data.message.strip()
    category, confidence, alternatives, emergency = classify_text(message)
    draft = dict(data.draft)
    draft["description"] = message
    if draft.get("category") in (None, "", "Other") and category != "Other":
        draft["category"] = category
    if not draft.get("title"):
        draft["title"] = " ".join(message.split()[:10]).strip().rstrip(".,!?")
    if not draft.get("location"):
        draft["location"] = user.hostel.name if user.hostel else ""
    if emergency:
        notify_roles(db, ("Administrator", "Super Admin"), SAFETY_MESSAGE)
        db.commit()
    reply = (
        SAFETY_MESSAGE if emergency else
        f"This may be a {category} issue ({confidence:.0%} confidence)."
        if confidence >= 0.6 else
        "I need one more detail to identify the right campus team. Please clarify the issue."
    )
    return IssueChatResponse(
        reply=reply,
        draft=draft,
        confidence=confidence,
        category=category,
        alternatives=alternatives,
        needs_review=confidence < 0.6,
        emergency=emergency,
    )


@router.post("/confirm", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def confirm_issue(
    data: IssueCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Student")),
) -> IssueResponse:
    return issue_to_response(create_issue(db, user, data))


@router.patch("/{token}/status", response_model=IssueResponse)
def patch_status(
    token: str,
    data: IssueUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IssueResponse:
    issue = get_issue(db, token)
    ensure_issue_access(issue, user)
    if user.role == "Student":
        if issue.status != "Resolved" or data.status != "Reopened":
            raise HTTPException(status_code=403, detail="Students may only reopen resolved complaints.")
        if not data.note.strip():
            raise HTTPException(status_code=422, detail="A reason is required to reopen a complaint.")
    elif user.role == "Department Staff":
        if data.status not in ("In Progress", "Resolved", "Reopened"):
            raise HTTPException(status_code=403, detail="Staff may update only assigned work.")
    elif user.role not in ("Administrator", "Super Admin", "Warden"):
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    return issue_to_response(update_status(db, issue, user, data.status, data.note.strip()))


@router.patch("/{token}/assignment", response_model=IssueResponse)
def patch_assignment(
    token: str,
    data: AssignmentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Administrator", "Super Admin", "Warden")),
) -> IssueResponse:
    issue = get_issue(db, token)
    ensure_issue_access(issue, user)
    if not data.staff_name:
        raise HTTPException(status_code=422, detail="A staff member is required.")
    return issue_to_response(assign_issue(db, issue, user, data.department, data.staff_name))


@router.post("/{token}/duplicates", response_model=IssueResponse)
def link_duplicate(
    token: str,
    data: DuplicateLinkRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("Administrator", "Super Admin")),
) -> IssueResponse:
    issue = get_issue(db, token)
    parent = get_issue(db, data.duplicate_of)
    if issue.id == parent.id:
        raise HTTPException(status_code=422, detail="A complaint cannot be linked to itself.")
    old_parent = issue.duplicate_of
    issue.duplicate_of = parent.id
    db.add(AuditEvent(
        issue_id=issue.id,
        actor_id=user.id,
        actor=user.name,
        action="Duplicate linked",
        detail=f"Linked to {parent.token}",
        old_value={"duplicateOf": old_parent},
        new_value={"duplicateOf": parent.token},
    ))
    db.commit()
    return issue_to_response(get_issue(db, token))
