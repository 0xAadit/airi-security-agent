from fastapi import APIRouter, HTTPException
from db import get_pool
from models import Tag, TagCreate, ItemTagCreate

router = APIRouter(tags=["tags"])


@router.get("/tags", response_model=list[Tag])
async def list_tags():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tags ORDER BY name ASC")
    return [dict(r) for r in rows]


@router.post("/tags", response_model=Tag)
async def create_tag(tag: TagCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO tags (name) VALUES ($1) RETURNING *", tag.name
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Tag already exists")
    return dict(row)


@router.post("/items/{item_id}/tags")
async def add_tag_to_item(item_id: int, req: ItemTagCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        item = await conn.fetchrow("SELECT id FROM items WHERE id = $1", item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        tag = await conn.fetchrow("SELECT id FROM tags WHERE id = $1", req.tag_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        try:
            await conn.execute(
                "INSERT INTO item_tags (item_id, tag_id) VALUES ($1, $2)",
                item_id,
                req.tag_id,
            )
        except Exception:
            # Already exists
            pass
    return {"status": "ok"}


@router.delete("/items/{item_id}/tags/{tag_id}")
async def remove_tag_from_item(item_id: int, tag_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute(
            "DELETE FROM item_tags WHERE item_id = $1 AND tag_id = $2", item_id, tag_id
        )
    if res == "DELETE 0":
        raise HTTPException(status_code=404, detail="Association not found")
    return {"status": "ok"}
