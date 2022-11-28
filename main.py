from typing import Union, List
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sql_app import crud, models, schemas
from sql_app.database import SessionLocal, engine
from sqlalchemy.orm import Session
import utils
from datetime import datetime, timedelta
from jose import jwt, JWTError
import os, time

models.Base.metadata.create_all(bind=engine)
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
os.environ['TZ'] = 'Asia/Hong_Kong'
time.tzset()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    uid: Union[int, None] = None

class CredentialData(BaseModel):
    email: str
    password: str

class FriendRequest(BaseModel):
    friend_user_id: int

class User(BaseModel):
    id: int

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"Hello":"World"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

def authenticate_user(email: str, password: str, db):
    user = crud.get_user_by_email(db, email)
    if not user:
        return False
    if not utils.verify_hashed_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, utils.JWT_SECRET_KEY, algorithm=utils.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db:Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, utils.JWT_SECRET_KEY, algorithms=[utils.ALGORITHM])
        uid: str = payload.get("sub")
        exp = payload.get("exp")
        if uid is None:
            raise credentials_exception
        if(int(round((datetime.now()).timestamp())) > int(round((datetime.fromtimestamp(exp)+timedelta(hours=-8)).timestamp()))):
            raise credentials_exception
        token_data = TokenData(uid=uid)
    except BaseException as e:
        print(e)
        raise credentials_exception
    user = crud.get_user(db, user_id=token_data.uid)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token",response_model=Token)
async def login_for_access_token(credential_data: CredentialData , db: Session = Depends(get_db)):
    user = authenticate_user(credential_data.email, credential_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/current/user",response_model=schemas.User)
async def get_current_user(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

@app.post("/make/friend/request") # invitation to new friend
async def make_friend_request(friend_request:FriendRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.id == friend_request.friend_user_id:
        return {"message":"Cannot make friend with yourself"}

    # check it is already sent
    friend = crud.get_user_friend(db, current_user.id, friend_request.friend_user_id)
    if friend:
        if friend.status == 0:
            return {"message":"Sent invitation already"}
        if friend.status == 1:
            return {"message":"Your guy become friend already"}

    # create friend request
    friend = crud.create_user_friend(db, friend_request.friend_user_id, current_user.id)
    return friend

@app.post("/accept/friend/request")
async def accept_friend_request(friend_request: FriendRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # find the request
    fr = crud.get_user_friend(db,friend_request.friend_user_id, current_user.id)

    if not fr:
        return {"message": "She/He has not send any invitation to you"}

    if fr.status == 1:
        return {"message": "You guys become friend already"}

    if fr.status == 0:
        fr.status = 1
        db.add(fr)
        db.commit()
        db.refresh(fr)
        return fr

@app.post("/my/friend/request")
async def get_friend_request(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    requests = crud.get_friend_request(db, current_user.id)
    return requests





