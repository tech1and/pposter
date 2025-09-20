# shop/tasks.py
import aiohttp
import asyncio
import logging
from decimal import Decimal, InvalidOperation
from django.conf import settings
from .models import Category, Item

from celery import shared_task

# Настройка логирования
logger = logging.getLogger(__name__)

YANDEX_API_URL = "https://api.content.market.yandex.ru/v3/affiliate/search"
HEADERS = {"Authorization": settings.YANDEX_MARKET_TOKEN}
DEFAULT_PARAMS = {
    "geo_id": 213,
    "clid": 3150664,
    "count": 30,
    "fields": (
        "MODEL_PRICE,MODEL_DEFAULT_OFFER,MODEL_SPECIFICATION,MODEL_PHOTO,MODEL_PHOTOS,OFFER_DELIVERY"
    ),
    "format": "json"
}

async def fetch_products(session: aiohttp.ClientSession, query: str, page: int = 1) -> dict:
    params = {**DEFAULT_PARAMS, "text": query, "page": page}
    try:
        async with session.get(YANDEX_API_URL, headers=HEADERS, params=params, timeout=10) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                logger.error(f"Yandex API Error {resp.status} for '{query}', page {page}")
                return {"status": "ERROR", "items": []}
    except Exception as e:
        logger.error(f"Exception for '{query}': {e}")
        return {"status": "ERROR", "items": []}

def to_decimal(val):
    try:
        return Decimal(str(val)) if val else None
    except (InvalidOperation, ValueError):
        return None

def extract_image_urls(photos_data):
    """Извлекает список URL изображений из поля 'photos'"""
    if not photos_data:
        return []
    urls = []
    for photo in photos_data:
        url = photo.get("url")
        if url:
            urls.append(url.strip())  # убираем лишние пробелы
    return urls

@shared_task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def sync_category_products_task(self, category_name: str):
    """Celery-задача: синхронизация товаров по категории."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_sync_worker(category_name))
    loop.close()

async def _sync_worker(category_name: str):
    async with aiohttp.ClientSession() as session:
        all_products = []
        for page in range(1, 6):  # макс. 5 страниц
            data = await fetch_products(session, category_name, page)
            if data.get("status") != "OK":
                break
            items = data.get("items", [])
            all_products.extend(items)

            total_pages = data["context"]["page"]["total"]
            if page >= total_pages:
                break

        if not all_products:
            logger.info(f"No products found for category '{category_name}'")
            return

        try:
            category = await Category.objects.aget(name=category_name)
        except Category.DoesNotExist:
            logger.error(f"Category '{category_name}' not found")
            return

        for item in all_products:
            specs = item.get("specifications")

            # Основное фото
            main_photo = (
                item.get("photo", {}).get("url") or
                (item.get("photos", [{}])[0].get("url") if item.get("photos") else None)
            )

            # Все фото — извлекаем только URL
            photos = item.get("photos", [])
            image_urls = extract_image_urls(photos)

            price_min = item.get("price", {}).get("min")
            price_max = item.get("price", {}).get("max")
            offer_price = item.get("offer", {}).get("price", {}).get("value")

            # Сохраняем товар
            await Item.objects.aupdate_or_create(
                external_id=item["id"],
                defaults={
                    "category": category,
                    "name": item["name"],
                    "description": item.get("description"),
                    "link": item.get("link", ""),
                    "price_min": to_decimal(price_min),
                    "price_max": to_decimal(price_max),
                    "offer_price": to_decimal(offer_price),
                    "specifications": specs,
                    "image_url": main_photo,
                    "images_all": image_urls,  # ← Сохраняем список URL
                    "offer_sku": item.get("offer", {}).get("sku"),
                }
            )

    logger.info(f"Synced {len(all_products)} products for category '{category_name}'")