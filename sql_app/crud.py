from sqlalchemy.orm import Session
import utils
from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_friend_request(db: Session, user_id):
    return db.query(models.Friend).filter(models.Friend.friend_user_id == user_id).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = utils.get_hashed_password(user.password)
    db_user = models.User(
        email=user.email, 
        hashed_password=hashed_password,
        first_name = user.first_name,
        last_name = user.last_name,
        phone = user.phone,
        profile_picture = user.profile_picture,
        company = user.company
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_user_friend(db: Session, friend_user_id, master_user_id, status=0):
    db_friend = models.Friend(
        friend_user_id = friend_user_id,
        master_user_id= master_user_id,
        status=status
    )
    db.add(db_friend)
    db.commit()
    db.refresh(db_friend)
    return db_friend

def get_user_friend(db: Session, master_user_id:int, friend_user_id: int):
    return db.query(models.Friend).filter(models.Friend.master_user_id == master_user_id).filter(models.Friend.friend_user_id == friend_user_id).first()

def update_user_friend(db: Session, master_user_id:int, friend_user_id: int, status: int):
    user = get_user(db, friend_user_id)

    if not user:
        return {"message":"this friend is not exist."}
    
    friend = get_user_friend(db, master_user_id, friend_user_id)

    if not friend:
        return {"message":"please make a friend first"}

    friend.status = status
    db.add(friend)
    db.commit()
    db.refresh(friend)
    return friend
    
