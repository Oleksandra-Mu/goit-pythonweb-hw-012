from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path,
    Request,
    UploadFile,
    File,
)
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis
from src.database.db import get_db
from src.schemas.users import ResponseUser, UserModel
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.upload_file import UploadFileService
from src.config.config import settings
from src.repository.users import update_avatar_url

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(auth_service.get_current_user)],
)

limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me",
    response_model=ResponseUser,
    description="No more than 10 requests per minute",
)
@limiter.limit("10/minute")
async def me(
    request: Request, user: ResponseUser = Depends(auth_service.get_current_user)
):
    return user


@router.patch("/avatar", response_model=ResponseUser)
async def update_avatar_user(
    file: UploadFile = File(),
    user: ResponseUser = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(lambda: Redis(host="localhost", port=6379, db=0)),
):
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.full_name)

    user = await update_avatar_url(user.email, avatar_url, db, redis_client)

    return user


# @router.get(
#     "/",
#     response_model=List[ResponseUser],
# )

# async def get_users(db: Session = Depends(get_db)):
#     users = await repository_users.get_users(db)
#     return users


# @router.get("/{user_id}", response_model=ResponseUser)
# async def get_user_by_id(user_id: int = Path(ge=1), db: Session = Depends(get_db)):
#     user = await repository_users.get_user_by_id(user_id, db)
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
#     return user


# @router.post("/", response_model=ResponseUser, status_code=status.HTTP_201_CREATED)
# async def create_user(body: UserModel, db: Session = Depends(get_db)):
#     user = await repository_users.create_user(body, db)
#     return user


# @router.put("/{user_id}", response_model=ResponseUser)
# async def update_user(
#     body: UserModel, user_id: int = Path(ge=1), db: Session = Depends(get_db)
# ):
#     user = await repository_users.update_user(body, user_id, db)
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
#     return user


# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def remove_user(user_id: int = Path(ge=1), db: Session = Depends(get_db)):
#     user = await repository_users.remove_user(user_id, db)
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
#     return user
