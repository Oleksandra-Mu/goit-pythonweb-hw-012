from sqlalchemy.orm import Session
from sqlalchemy import extract, or_
from datetime import datetime, timedelta
from src.database.models import Contacts
from src.schemas.contact import ContactCreate, ContactUpdate


async def create_contact(body: ContactCreate, db: Session):
    contact = Contacts(**body.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


async def get_contacts(limit: int, offset: int, user_id: int, db: Session):
    contacts = (
        db.query(Contacts)
        .filter(Contacts.user_id == user_id)
        .limit(limit)
        .offset(offset)
        .all()
    )
    return contacts


async def get_contact(contact_id: int, db: Session):
    contact = db.query(Contacts).filter_by(id=contact_id).first()
    return contact


async def update_contact(body: ContactUpdate, contact_id: int, db: Session):
    contact = db.query(Contacts).filter_by(id=contact_id).first()
    if contact:
        for key, value in body.model_dump().items():
            setattr(contact, key, value)
        db.commit()
        db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, db: Session):
    contact = db.query(Contacts).filter_by(id=contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact


def search_contacts(db: Session, query: str):
    return (
        db.query(Contacts)
        .filter(
            (Contacts.name.ilike(f"%{query}%"))
            | (Contacts.email.ilike(f"%{query}%"))
            | (Contacts.phone_number.ilike(f"%{query}%"))
        )
        .all()
    )


async def get_upcoming_birthdays(db: Session):
    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    today_month = today.month
    today_day = today.day
    week_later_month = week_later.month
    week_later_day = week_later.day

    if today_month == week_later_month:
        return (
            db.query(Contacts)
            .filter(
                extract("month", Contacts.date_of_birth) == today_month,
                extract("day", Contacts.date_of_birth).between(
                    today_day, week_later_day
                ),
            )
            .all()
        )
    else:
        return (
            db.query(Contacts)
            .filter(
                or_(
                    (extract("month", Contacts.date_of_birth) == today_month)
                    & (extract("day", Contacts.date_of_birth) >= today_day),
                    (extract("month", Contacts.date_of_birth) == week_later_month)
                    & (extract("day", Contacts.date_of_birth) <= week_later_day),
                )
            )
            .all()
        )
