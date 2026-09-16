from fastapi import APIRouter, HTTPException
from db import get_pool
from models import Item, ItemCreate, ItemUpdate

router = APIRouter(tags=["items"])


@router.get("/search", response_model=list[Item])
async def search(q: str = ""):
    pool = await get_pool()
    async with pool.acquire() as conn:
        # VULNERABLE: f-string LIKE concatenation
        query = f"SELECT * FROM items WHERE name LIKE '%{q}%' ORDER BY id ASC"
        rows = await conn.fetch(query)
    return [dict(r) for r in rows]


@router.get("/items", response_model=list[Item])
async def list_items(
    status: str | None = None,
    priority: str | None = None,
    owner_id: int | None = None,
    tag: str | None = None,
):
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT i.* FROM items i "
        params = []
        conditions = []

        if tag:
            query += "JOIN item_tags it ON i.id = it.item_id "
            query += "JOIN tags t ON it.tag_id = t.id "
            params.append(tag)
            conditions.append(f"t.name = ${len(params)}")

        if status:
            params.append(status)
            conditions.append(f"i.status = ${len(params)}")

        if priority:
            params.append(priority)
            conditions.append(f"i.priority = ${len(params)}")

        if owner_id is not None:
            params.append(owner_id)
            conditions.append(f"i.owner_id = ${len(params)}")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY i.id ASC"

        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


@router.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO items (name, description, status, priority, owner_id)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            """,
            item.name,
            item.description,
            item.status,
            item.priority,
            item.owner_id,
        )
    return dict(row)


@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return dict(row)


@router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemUpdate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        current = await conn.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
        if not current:
            raise HTTPException(status_code=404, detail="Item not found")

        updates = []
        params = []

        for field, value in item.model_dump(exclude_unset=True).items():
            params.append(value)
            updates.append(f"{field} = ${len(params)}")

        if not updates:
            return dict(current)

        params.append(item_id)
        updates.append("updated_at = now()")

        query = f"UPDATE items SET {', '.join(updates)} WHERE id = ${len(params)} RETURNING *"
        row = await conn.fetchrow(query, *params)

    return dict(row)


@router.delete("/items/{item_id}")
async def delete_item(item_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("DELETE FROM items WHERE id = $1", item_id)
    if res == "DELETE 0":
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "ok"}
