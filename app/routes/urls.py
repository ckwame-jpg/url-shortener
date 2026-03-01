import string
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import URL, User
from app.schemas import URLCreate, URLOut
from app.auth import get_current_user
from app.redis_client import redis_client

router = APIRouter()

CACHE_TTL = 60 * 60 * 24  # 24 hours


def generate_short_code(length: int = 7) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


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

    try:
        redis_client.set(f"url:{short_code}", url.original_url, ex=CACHE_TTL)
    except Exception:
        pass  # Redis down shouldn't break URL creation

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

    try:
        redis_client.delete(f"url:{short_code}")
    except Exception:
        pass


@router.get("/{short_code}")
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    # Try Redis cache first
    original_url = None
    url_id = None

    try:
        original_url = redis_client.get(f"url:{short_code}")
        cached_id = redis_client.get(f"url_id:{short_code}")
        if cached_id:
            url_id = int(cached_id)
    except Exception:
        pass

    if not original_url:
        url = db.query(URL).filter(URL.short_code == short_code).first()
        if not url:
            raise HTTPException(status_code=404, detail="Short URL not found")
        original_url = url.original_url
        url_id = url.id

        try:
            redis_client.set(f"url:{short_code}", original_url, ex=CACHE_TTL)
            redis_client.set(f"url_id:{short_code}", str(url_id), ex=CACHE_TTL)
        except Exception:
            pass

    # Fire async click tracking
    if url_id:
        try:
            from app.tasks import process_click
            process_click.delay(
                url_id=url_id,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                referrer=request.headers.get("referer"),
            )
        except Exception:
            pass  # Worker down shouldn't break redirects

    return RedirectResponse(url=original_url, status_code=307)
