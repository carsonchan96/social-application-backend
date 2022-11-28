from typing import List, Union

from pydantic import BaseModel


class FriendBase(BaseModel):
    master_user_id: int
    friend_user_id: int
    status: int

class FriendCreate(FriendBase):
    pass


class Friend(FriendBase):
    id: int
    master_user_id: int
    friend_user_id: int
    status: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: str
    profile_picture: str
    company: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    friends: List[Friend] = []

    class Config:
        orm_mode = True
