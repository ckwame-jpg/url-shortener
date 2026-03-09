import secrets
import string

from celery.exceptions import CeleryError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import URL, User
from app.redis_client import redis_client
from app.schemas import URLCreate, URLOut

router = APIRouter()

CACHE_TTL = 60 * 60 * 24  # 24 hours


def generate_short_code(length: int = 7) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def cache_set(short_code: str, original_url: str, url_id: int | None = None):
    try:
        redis_client.set(f"url:{short_code}", original_url, ex=CACHE_TTL)
        if url_id is not None:
            redis_client.set(f"url_id:{short_code}", str(url_id), ex=CACHE_TTL)
    except RedisError:
        return


def cache_get(short_code: str) -> tuple[str | None, int | None]:
    try:
        original_url = redis_client.get(f"url:{short_code}")
        cached_id = redis_client.get(f"url_id:{short_code}")
        url_id = int(cached_id) if cached_id else None
        return original_url, url_id
    except (RedisError, ValueError, TypeError):
        return None, None


def cache_delete(short_code: str):
    try:
        redis_client.delete(f"url:{short_code}", f"url_id:{short_code}")
    except RedisError:
        return


def enqueue_click_tracking(request: Request, url_id: int):
    try:
        from app.tasks import process_click

        process_click.delay(
            url_id=url_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
        )
    except CeleryError:
        return


@router.post("/shorten", response_model=URLOut, status_code=status.HTTP_201_CREATED)
def shorten_url(
    payload: URLCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    short_code = generate_short_code()
    while db.query(URL).filter(URL.short_code == short_code).first():
        short_code = generate_short_code()

    url = URL(
        short_code=short_code,
        original_url=str(payload.original_url),
        user_id=current_user.id,
    )
    db.add(url)
    db.commit()
    db.refresh(url)

    cache_set(short_code, url.original_url, url.id)
    return url


@router.get("/urls", response_model=list[URLOut])
def list_urls(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(URL).filter(URL.user_id == current_user.id).order_by(URL.created_at.desc()).all()


@router.delete("/urls/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    url = db.query(URL).filter(URL.short_code == short_code, URL.user_id == current_user.id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    db.delete(url)
    db.commit()
    cache_delete(short_code)


@router.get("/{short_code}")
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    original_url, url_id = cache_get(short_code)

    if not original_url:
        url = db.query(URL).filter(URL.short_code == short_code).first()
        if not url:
            raise HTTPException(status_code=404, detail="Short URL not found")
        original_url = url.original_url
        url_id = url.id
        cache_set(short_code, original_url, url_id)

    if url_id is not None:
        enqueue_click_tracking(request, url_id)

    return RedirectResponse(url=original_url, status_code=307)
