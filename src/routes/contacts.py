from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas.contact import ContactUpdate, ContactCreate, Contact
from src.repository import contact as repository_contact
from src.database.models import Users
from src.services.auth import auth_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/",
    response_model=List[Contact],
)
async def get_contacts(
    limit: int = Query(10, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Users = Depends(auth_service.get_current_user),
):
    contacts = await repository_contact.get_contacts(limit, offset, current_user.id, db)
    return contacts


@router.get("/{contact_id}", response_model=Contact)
async def get_contact(
    contact_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _: Users = Depends(auth_service.get_current_user),
):
    contact = await repository_contact.get_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.post("/", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(auth_service.get_current_user),
):
    body_data = body.model_dump()
    body_data["user_id"] = current_user.id
    contact = await repository_contact.create_contact(ContactCreate(**body_data), db)
    return contact


@router.put("/{contact_id}", response_model=Contact)
async def update_contact(
    body: ContactUpdate,
    contact_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _: Users = Depends(auth_service.get_current_user),
):
    contact = await repository_contact.update_contact(body, contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_contact(
    contact_id: int = Path(ge=1),
    db: Session = Depends(get_db),
    _: Users = Depends(auth_service.get_current_user),
):
    contact = await repository_contact.remove_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return contact


@router.get("/search/", response_model=List[Contact])
def search_contacts_by_query(
    query: str,
    db: Session = Depends(get_db),
    _: Users = Depends(auth_service.get_current_user),
):
    search_result = repository_contact.search_contacts(db, query)
    if not search_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No contacts found"
        )
    return search_result


@router.get("/birthdays/", response_model=List[Contact])
async def get_birthdays(
    db: Session = Depends(get_db), _: Users = Depends(auth_service.get_current_user)
):
    upcoming_birthdays = await repository_contact.get_upcoming_birthdays(db)
    if not upcoming_birthdays:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No upcoming birthdays found"
        )
    return upcoming_birthdays
