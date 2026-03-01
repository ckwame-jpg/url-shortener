from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import URL, Click, User
from app.schemas import URLStats, ClickOut
from app.auth import get_current_user

router = APIRouter()


@router.get("/urls/{short_code}/stats", response_model=URLStats)
def get_url_stats(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    url = db.query(URL).filter(URL.short_code == short_code, URL.user_id == current_user.id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    clicks = db.query(Click).filter(Click.url_id == url.id).order_by(Click.clicked_at.desc()).all()

    referrers = Counter(c.referrer for c in clicks if c.referrer)
    top_referrers = [{"referrer": r, "count": n} for r, n in referrers.most_common(10)]

    devices = Counter(c.device_type for c in clicks if c.device_type)
    countries = Counter(c.country for c in clicks if c.country)

    return URLStats(
        short_code=url.short_code,
        original_url=url.original_url,
        total_clicks=url.click_count or 0,
        recent_clicks=[ClickOut.model_validate(c) for c in clicks[:20]],
        top_referrers=top_referrers,
        devices=dict(devices),
        countries=dict(countries),
    )
