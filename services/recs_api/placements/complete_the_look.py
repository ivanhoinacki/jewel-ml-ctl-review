import logging

from fastapi import APIRouter, Query
from pymongo import DESCENDING, MongoClient

from recs_api.settings import settings
from recs_api.ranking import score_candidates

router = APIRouter()
log = logging.getLogger(__name__)

client = MongoClient(
    settings.mongo_uri,
    serverSelectionTimeoutMS=settings.mongo_timeout_ms,
    socketTimeoutMS=settings.mongo_timeout_ms,
    connectTimeoutMS=settings.mongo_timeout_ms,
)
catalog = client[settings.mongo_db]["catalog"]

MAX_LIMIT = 48
CANDIDATE_FIELDS = {"sku": 1, "title": 1, "url": 1, "image": 1, "price": 1, "currency": 1, "brand": 1, "popularity": 1}


def _render_item(c: dict) -> dict | None:
    sku = c.get("sku")
    url = c.get("url")
    image_url = (c.get("image") or {}).get("url")
    if not sku or not url or not image_url:
        return None
    title = c.get("title") or ""
    price = c.get("price")
    return {
        "sku": sku,
        "title": title,
        "url": url,
        "image": {"url": image_url, "alt": title},
        "price": {
            "amount": price if isinstance(price, (int, float)) else None,
            "currency": c.get("currency") or settings.default_currency,
        },
        "brand": c.get("brand") or "",
    }


@router.get("/v1/{integration_id}/complete-the-look")
def complete_the_look(
    integration_id: str,
    sku: str,
    shopper_id: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=MAX_LIMIT),
):
    anchor = catalog.find_one({"integration_id": integration_id, "sku": sku})
    category = (anchor or {}).get("category")
    if not category:
        log.debug("complete-the-look empty integration=%s sku=%s reason=no-anchor-category", integration_id, sku)
        return {"items": []}

    candidates = list(
        catalog.find(
            {"integration_id": integration_id, "category": category, "sku": {"$ne": sku}},
            projection=CANDIDATE_FIELDS,
        )
        .sort("popularity", DESCENDING)
        .limit(settings.candidate_cap)
    )
    ranked = score_candidates(anchor, candidates, shopper_id=shopper_id)

    items = []
    for c in ranked:
        item = _render_item(c)
        if item is None:
            continue
        items.append(item)
        if len(items) == limit:
            break

    log.debug("complete-the-look served integration=%s sku=%s candidates=%d items=%d", integration_id, sku, len(candidates), len(items))
    return {"items": items}
