import argparse
import getpass
from uuid import uuid4

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.user import User

ROLES = ("Student", "Warden", "Administrator", "Department Staff", "Super Admin")


def create_user(role: str) -> None:
    email = input("Institute email: ").strip().casefold()
    scholar_no = input("Scholar number (optional): ").strip() or None
    name = input("Full name: ").strip()
    password = getpass.getpass("Password (minimum 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12 or password != confirmation:
        raise SystemExit("Passwords must match and be at least 12 characters.")

    factory = get_session_factory()
    with factory() as db:
        exists = db.scalar(select(User.id).where(User.email == email))
        if exists:
            raise SystemExit("That email already has an account.")
        user = User(
            id=str(uuid4()),
            email=email,
            scholar_no=scholar_no,
            name=name,
            role=role,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()
    print(f"Created {role} account for {email}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="CampusAlly account administration")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create-user", help="Create an account without public registration")
    create_parser.add_argument("--role", choices=ROLES, default="Student")
    args = parser.parse_args()
    if args.command == "create-user":
        create_user(args.role)


if __name__ == "__main__":
    main()
