from fastapi import APIRouter, HTTPException
from db import get_pool
from models import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # VULNERABLE: raw f-string concatenation
        query = (
            f"SELECT id FROM users "
            f"WHERE username = '{req.username}' AND password = '{req.password}'"
        )
        row = await conn.fetchrow(query)

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return LoginResponse(token=f"token-{row['id']}")
