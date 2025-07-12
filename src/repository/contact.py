from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_, select
from datetime import datetime, timedelta
from src.database.models import Contacts, Users
from src.schemas.contact import ContactCreate, ContactUpdate
from sqlalchemy import select


async def create_contact(body: ContactCreate, db: AsyncSession):
    """Create a new contact.

    This helper persists a new :class:`src.database.models.Contacts` ORM object
    to the database using the validated *body* data supplied by the API layer.

    Args:
        body (ContactCreate): Pydantic schema with contact data.
        db (AsyncSession): An active SQLAlchemy session obtained from a FastAPI
            dependency.

    Returns:
        Contacts: A freshly-created contact instance with primary key and
        relationships fully populated.
    """
    contact = Contacts(**body.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def get_contacts(limit: int, offset: int, user_id: int, db: AsyncSession):
    """Return paginated contacts for the specified user.

    Args:
        limit (int): Maximum number of contacts to return.
        offset (int): Offset for pagination.
        user_id (int): Owner's user id (FK in contacts table).
        db (AsyncSession): SQLAlchemy session.

    Returns:
        list[Contacts]: A list of contact objects belonging to *user_id*.
    """
    stmt = (
        select(Contacts).where(Contacts.user_id == user_id).limit(limit).offset(offset)
    )
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts


async def get_contact(contact_id: int, db: AsyncSession):
    """Fetch a single contact by its identifier.

    Args:
        contact_id (int): Primary key of the contact.
        db (AsyncSession): SQLAlchemy session.

    Returns:
        Contacts | None: The contact if it exists, *None* otherwise.
    """
    stmt = select(Contacts).where(Contacts.id == contact_id)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def update_contact(body: ContactUpdate, contact_id: int, db: AsyncSession):
    """Update an existing contact record.

    Args:
        body (ContactUpdate): Partial contact data used for update.
        contact_id (int): Identifier of the contact to update.
        db (AsyncSession): SQLAlchemy session.

    Returns:
        Contacts | None: Updated contact or *None* if not found.
    """
    stmt = select(Contacts).where(Contacts.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        for key, value in body.model_dump().items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)
    return contact


async def remove_contact(contact_id: int, db: AsyncSession):
    """Delete a contact from the database.

    Args:
        contact_id (int): Primary key of the contact to delete.
        db (AsyncSession): SQLAlchemy session.

    Returns:
        Contacts | None: Deleted contact instance for auditing or *None* if
        nothing matched the supplied id.
    """
    stmt = select(Contacts).where(Contacts.id == contact_id)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        await db.delete(contact)
        await db.commit()
    return contact


async def search_contacts(db: AsyncSession, query: str):
    """Perform a case-insensitive search across contacts' name, email and phone fields.

    Args:
        db (AsyncSession): Active SQLAlchemy async session.
        query (str): Substring to search for (case-insensitive).

    Returns:
        list[Contacts]: Contacts that match the search criteria.
    """
    stmt = select(Contacts).where(
        or_(
            Contacts.name.ilike(f"%{query}%"),
            Contacts.email.ilike(f"%{query}%"),
            Contacts.phone_number.ilike(f"%{query}%"),
        )
    )
    print(f"DEBUG: Generated statement (repr): {repr(stmt)}")
    result = await db.execute(stmt)
    contacts = result.scalars().all()
    return contacts


async def get_upcoming_birthdays(db: AsyncSession):
    """Return contacts whose birthday occurs within the next 7 days.

    Args:
        db (AsyncSession): Active SQLAlchemy async session.

    Returns:
        list[Contacts]: Contacts having birthdays in the next week.
    """
    today = datetime.now().date()
    week_later = today + timedelta(days=7)

    today_month = today.month
    today_day = today.day
    week_later_month = week_later.month
    week_later_day = week_later.day

    if today_month == week_later_month:
        stmt = select(Contacts).where(
            extract("month", Contacts.date_of_birth) == today_month,
            extract("day", Contacts.date_of_birth).between(today_day, week_later_day),
        )
    else:
        stmt = select(Contacts).where(
            or_(
                (extract("month", Contacts.date_of_birth) == today_month)
                & (extract("day", Contacts.date_of_birth) >= today_day),
                (extract("month", Contacts.date_of_birth) == week_later_month)
                & (extract("day", Contacts.date_of_birth) <= week_later_day),
            )
        )
    result = await db.execute(stmt)
    return result.scalars().all()
