import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from functools import partial
from datetime import date

from src.database.models import Contacts, Users
from src.repository.contact import (
    create_contact,
    get_contacts,
    get_contact,
    update_contact,
    remove_contact,
    search_contacts,
    get_upcoming_birthdays,
)
from src.schemas.contact import ContactModel, ContactCreate, ContactUpdate


@pytest.fixture
def mock_session():
    """Fixture to create a mock SQLAlchemy session."""
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contact_repository(mock_session):
    """Fixture to create a mock contact repository."""
    return {
        "create_contact": partial(create_contact, db=mock_session),
        "get_contacts": partial(get_contacts, db=mock_session),
        "get_contact": partial(get_contact, db=mock_session),
        "update_contact": partial(update_contact, db=mock_session),
        "remove_contact": partial(remove_contact, db=mock_session),
        "search_contacts": partial(search_contacts, db=mock_session),
        "get_upcoming_birthdays": partial(get_upcoming_birthdays, db=mock_session),
    }


@pytest.fixture
def user():
    """Fixture to create a mock user."""
    return Users(id=1, full_name="testuser", roles="user")


@pytest.fixture
def contact():
    """Fixture to create a mock contact."""
    return Contacts(
        id=1,
        name="John Doe",
        email="john@example.com",
        phone_number="+1234567890",
        date_of_birth=date(1990, 7, 1),
        user_id=1,
    )


@pytest.fixture
def contact_create_schema():
    """Fixture to create mock contact creation data."""
    return ContactCreate(
        name="Jane Doe",
        email="jane@example.com",
        phone_number="+380987654321",
        date_of_birth=date(1992, 7, 12),
        user_id=1,
    )


@pytest.fixture
def contact_update_schema():
    """Fixture to create mock contact update data."""
    return ContactUpdate(
        name="Jane Smith",
        email="smith@example.com",
        phone_number="+1122334455",
        date_of_birth=date(1993, 3, 3),
        user_id=1,
    )


@pytest.mark.asyncio
async def test_create_contact(contact_repository, mock_session, contact_create_schema):
    """Test creating a new contact."""

    result = await contact_repository["create_contact"](body=contact_create_schema)

    assert isinstance(result, Contacts)
    assert result.name == contact_create_schema.name
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_get_contacts(contact_repository, mock_session, user, contact):
    """Test fetching contacts for a user."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contact_repository["get_contacts"](
        limit=10,
        offset=0,
        user_id=user.id,
    )

    assert len(contacts) == 1
    assert contacts[0].name == "John Doe"


@pytest.mark.asyncio
async def test_get_contact(contact_repository, mock_session, contact):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    one_contact = await contact_repository["get_contact"](contact_id=1)
    assert one_contact is not None
    assert one_contact.id == 1
    assert one_contact.name == "John Doe"


@pytest.mark.asyncio
async def test_update_contact(
    contact_repository, mock_session, contact, contact_update_schema
):
    """Test updating an existing contact."""

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    updated_contact = await contact_repository["update_contact"](
        body=contact_update_schema,
        contact_id=1,
    )

    assert updated_contact is not None
    assert updated_contact.name == "Jane Smith"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(updated_contact)


@pytest.mark.asyncio
async def test_remove_contact(contact_repository, mock_session, contact):
    """Test removing a contact."""
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    await contact_repository["remove_contact"](contact_id=1)

    mock_session.delete.assert_awaited_once_with(contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_contacts(contact_repository, mock_session, contact):
    """Test searching contacts."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock_result)

    results = await contact_repository["search_contacts"](query="John")

    assert len(results) == 1
    assert results[0].name == "John Doe"


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(contact_repository, mock_session, contact):
    """Test getting upcoming birthdays."""
    contact.date_of_birth = date(1990, 7, 13)

    with patch("src.repository.contact.datetime") as mock_datetime:
        mock_datetime.now.return_value.date.return_value = date(2025, 7, 11)

        def scalars_mock():
            if (
                contact.date_of_birth.month == 7
                and 11 <= contact.date_of_birth.day <= 18
            ):
                return MagicMock(all=MagicMock(return_value=[contact]))
            return MagicMock(all=MagicMock(return_value=[]))

        mock_result = MagicMock()
        mock_result.scalars.side_effect = scalars_mock
        mock_session.execute = AsyncMock(return_value=mock_result)

        results = await contact_repository["get_upcoming_birthdays"]()

        assert len(results) == 1
        assert results[0].name == "John Doe"
