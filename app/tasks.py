from __future__ import annotations

from typing import Optional
from user_agents import parse
from app.celery_app import celery
from app.database import SessionLocal
from app.models import Click, URL


def parse_device_type(user_agent_string: Optional[str]) -> str:
    if not user_agent_string:
        return "unknown"
    ua = parse(user_agent_string)
    if ua.is_mobile:
        return "mobile"
    if ua.is_tablet:
        return "tablet"
    if ua.is_pc:
        return "desktop"
    if ua.is_bot:
        return "bot"
    return "other"


@celery.task(name="process_click")
def process_click(url_id: int, ip_address: Optional[str], user_agent: Optional[str], referrer: Optional[str]):
    db = SessionLocal()
    try:
        device_type = parse_device_type(user_agent)

        click = Click(
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            device_type=device_type,
            country=None,  # Could add IP geolocation later
        )
        db.add(click)

        url = db.query(URL).filter(URL.id == url_id).first()
        if url:
            url.click_count = (url.click_count or 0) + 1

        db.commit()
    finally:
        db.close()
