from fastapi import APIRouter, HTTPException
from db import get_pool
from models import UserResponse

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserResponse])
async def list_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Don't select password
        rows = await conn.fetch(
            "SELECT id, username, email, created_at FROM users ORDER BY id ASC"
        )
    return [dict(r) for r in rows]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, username, email, created_at FROM users WHERE id = $1", user_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)
