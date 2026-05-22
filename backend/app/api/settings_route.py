"""
Settings API - App configuration management
"""

import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.constants import RuntimeSettings

logger = logging.getLogger(__name__)
router = APIRouter()


class SettingsUpdate(BaseModel):
    base_currency: Optional[str] = None
    receipt_threshold: Optional[float] = None
    anomaly_threshold_zscore: Optional[float] = None
    openai_api_key: Optional[str] = None
    ai_provider: Optional[str] = None


@router.get("/settings")
async def get_settings():
    return RuntimeSettings.get_all()


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    if update.base_currency:
        RuntimeSettings.set("base_currency", update.base_currency.upper())
    if update.receipt_threshold is not None:
        RuntimeSettings.set("receipt_threshold", update.receipt_threshold)
    if update.anomaly_threshold_zscore is not None:
        RuntimeSettings.set("anomaly_threshold_zscore", update.anomaly_threshold_zscore)
    if update.openai_api_key:
        RuntimeSettings.set("openai_key_configured", True)
    if update.ai_provider is not None:
        if update.ai_provider in ("groq", "none", "openai"):
            RuntimeSettings.set("ai_provider", update.ai_provider)
    return {"status": "updated", "settings": RuntimeSettings.get_all()}


@router.post("/settings/vendors")
async def add_vendor_mapping(canonical: str, aliases: list[str]):
    vendors = RuntimeSettings.get("vendors", {})
    vendors[canonical.lower()] = {
        "canonical": canonical,
        "aliases": [a.lower() for a in aliases],
    }
    RuntimeSettings.set("vendors", vendors)
    return {"status": "added", "canonical": canonical}


@router.get("/settings/exchange-rates")
async def get_exchange_rates():
    return RuntimeSettings.get("exchange_rates", {})


@router.post("/settings/exchange-rates")
async def update_exchange_rate(currency: str, rate: float):
    rates = RuntimeSettings.get("exchange_rates", {})
    rates[currency.upper()] = rate
    RuntimeSettings.set("exchange_rates", rates)
    return {"status": "updated", "currency": currency.upper(), "rate": rate}
