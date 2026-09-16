from datetime import datetime
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    status: str = "open"
    priority: str = "medium"
    owner_id: int | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    owner_id: int | None = None


class Item(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str = "open"
    priority: str = "medium"
    owner_id: int | None = None
    created_at: datetime
    updated_at: datetime


class CommentCreate(BaseModel):
    author_id: int
    body: str


class Comment(BaseModel):
    id: int
    item_id: int
    author_id: int
    body: str
    created_at: datetime


class TagCreate(BaseModel):
    name: str


class Tag(BaseModel):
    id: int
    name: str


class ItemTagCreate(BaseModel):
    tag_id: int
