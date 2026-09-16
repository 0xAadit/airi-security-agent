from contextlib import asynccontextmanager
from fastapi import FastAPI
from db import init_db
from routers import auth, items, comments, tags, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(items.router)
app.include_router(comments.router)
app.include_router(tags.router)
app.include_router(users.router)
