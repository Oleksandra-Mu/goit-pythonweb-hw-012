from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path,
    Query,
    Request,
    BackgroundTasks,
)
from fastapi.security import OAuth2PasswordRequestForm

from typing import List

from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas.users import (
    UserModelRegister,
    TokenModel,
    RequestEmail,
    ResetPasswordRequest,
    ResetPasswordConfirm,
)
from src.repository import users as repository_users
from src.repository.auth import Hash
from src.services.auth import auth_service
from src.services.email import send_email, send_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])
hash_handler = Hash()


@router.post(
    "/signup", response_model=UserModelRegister, status_code=status.HTTP_201_CREATED
)
async def signup(
    body: UserModelRegister,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new user and send a confirmation email.

    Parameters
    ----------
    body : UserModelRegister
        User registration data (email, password, etc.).
    background_tasks : BackgroundTasks
        FastAPI background tasks manager for sending email asynchronously.
    request : Request
        The current request instance; used to build base URL for email.
    db : Session, optional
        SQLAlchemy session dependency injected by FastAPI.

    Returns
    -------
    UserModelRegister
        The newly created user object.
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(
        send_email, new_user.email, new_user.full_name, str(request.base_url)
    )
    return new_user


@router.post("/login", response_model=TokenModel)
async def login(
    body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Authenticate user and return a JWT access token.

    Parameters
    ----------
    body : OAuth2PasswordRequestForm
        Form containing *username* (email) and *password* fields.
    db : Session, optional
        SQLAlchemy session dependency injected by FastAPI.

    Returns
    -------
    dict
        A dictionary with `access_token` and `token_type` keys.
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email"
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed"
        )
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password"
        )

    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(
    token: str,
    db: Session = Depends(get_db),
):
    """Activate user account using email confirmation token."""
    email = auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.change_confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """Resend the email confirmation link to the user.

    Parameters
    ----------
    body : RequestEmail
        Schema containing the user's email address.
    background_tasks : BackgroundTasks
        FastAPI background tasks manager to schedule sending the email.
    request : Request
        Current request instance to build base URL for email link.
    db : Session, optional
        SQLAlchemy session dependency injected by FastAPI.

    Returns
    -------
    dict
        A message informing that the confirmation email has been (re)sent.
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user:
        if user.confirmed:
            return {"message": "Your email is already confirmed"}
        background_tasks.add_task(
            send_email, user.email, user.full_name, str(request.base_url)
        )
    return {"message": "Check your email for confirmation."}


@router.post("/reset_password_request")
async def reset_password_request(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """Send a password-reset email containing a one-time token.

    Parameters
    ----------
    body : ResetPasswordRequest
        Schema with the user's email requesting the reset.
    background_tasks : BackgroundTasks
        FastAPI background tasks manager for sending email asynchronously.
    request : Request
        Current request instance to build base URL for reset link.
    db : Session, optional
        SQLAlchemy session dependency injected by FastAPI.

    Returns
    -------
    dict
        A message indicating that the reset email has been sent.
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    reset_token = await auth_service.create_access_token(
        data={"sub": user.email, "token_scope": "reset_password"}, expires_delta=3600
    )

    background_tasks.add_task(
        send_reset_email,
        user.email,
        user.full_name,
        str(request.base_url),
        reset_token,
    )
    return {"message": "Password reset email sent"}


@router.post("/reset_password")
async def reset_password(
    body: ResetPasswordConfirm,
    db: Session = Depends(get_db),
):
    """Update password using a valid reset token."""
    email = auth_service.get_email_from_token(body.token)
    user = await repository_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    hashed_password = auth_service.get_password_hash(body.new_password)
    await repository_users.update_user_password(user.email, hashed_password, db)

    return {"message": "Password updated successfully"}
