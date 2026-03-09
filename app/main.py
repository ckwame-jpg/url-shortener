from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import URL, User  # noqa: F401
from app.routes import analytics, urls, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield


def seed_demo_data():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "demo@shortener.dev").first():
            demo_user = User(
                email="demo@shortener.dev",
                hashed_password=hash_password("demo1234"),
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

            demo_url = URL(
                short_code="demo123",
                original_url="https://github.com/ckwame-jpg",
                user_id=demo_user.id,
            )
            db.add(demo_url)
            db.commit()
    finally:
        db.close()


app = FastAPI(title="URL Shortener", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(urls.router)
app.include_router(analytics.router)
