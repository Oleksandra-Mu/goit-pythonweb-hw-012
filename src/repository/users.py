from sqlalchemy.orm import Session
from redis import Redis
from src.database.models import Users
from src.schemas.users import UserModel


# async def get_users(db: Session):
#     users = db.query(Users).all()
#     return users


# async def get_user_by_id(user_id: int, db: Session):
#     user = db.query(Users).filter_by(id=user_id).first()
#     return user


async def get_user_by_email(email: str, db: Session):
    user = db.query(Users).filter_by(email=email).first()
    return user


async def create_user(body: UserModel, db: Session):
    user = Users(**body.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# async def update_user(body: UserModel, user_id: int, db: Session):
#     user = db.query(Users).filter_by(id=user_id).first()
#     if user:
#         user.email = body.email
#         db.commit()
#     return user


# async def remove_user(user_id: int, db: Session):
#     user = db.query(Users).filter_by(id=user_id).first()
#     if user:
#         db.delete(user)
#         db.commit()
#     return user


async def update_token(user: Users, refresh_token, db: Session):
    user.refresh_token = refresh_token
    db.commit()


async def change_confirmed_email(email: str, db: Session) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    db.commit()


async def update_avatar_url(
    email: str, url: str, db: Session, redis_client: Redis = None
):
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    db.refresh(user)
    if redis_client:
        redis_client.delete(f"user:{email}")
    return user
