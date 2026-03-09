from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class URLCreate(BaseModel):
    original_url: str


class URLOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime


class ClickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    clicked_at: datetime
    ip_address: Optional[str]
    referrer: Optional[str]
    country: Optional[str]
    device_type: Optional[str]


class URLStats(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    recent_clicks: List[ClickOut]
    top_referrers: List[Dict]
    devices: Dict[str, int]
    countries: Dict[str, int]
