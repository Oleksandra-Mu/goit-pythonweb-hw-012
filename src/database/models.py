"""SQLAlchemy ORM models representing application entities."""

import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from src.database.db import Base


class Role(enum.Enum):
    """Enumeration of application roles."""
    admin: str = "admin"
    user: str = "user"


class Users(Base):
    """Table storing registered users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(150), nullable=False)
    full_name = Column(String(100), nullable=False)
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    roles = Column("roles", Enum(Role), default=Role.user)


class Contacts(Base):
    """Table containing user contact records."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String(150), nullable=False)
    phone_number = Column(String(20), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    additional_info = Column(String(500), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("Users", backref="contacts")
