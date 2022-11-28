from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TEXT
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    first_name = Column(String)
    last_name= Column(String)
    phone = Column(String)
    profile_picture = Column(TEXT)
    company = Column(String)
    friends = relationship("Friend", back_populates="master_user")

class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    master_user_id = Column(Integer, ForeignKey("users.id"))
    friend_user_id = Column(Integer)
    status = Column(Integer, default=0) #0=pending, 1=acccepted, 2=deleted, 3=rejected
    master_user = relationship("User", back_populates="friends")
