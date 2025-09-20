from django import template
from shop.models import Item
import random
from django.db.models import Max


register = template.Library()

@register.simple_tag
def random_item():
    """Возвращает случайный товар модели Item, или None, если нет товаров. Оптимизированная версия."""
    max_id = Item.objects.aggregate(Max('id'))['id__max']
    if max_id is None:
         return None
    random_id = random.randint(1, max_id) # Предполагаем, что id начинаются с 1
    item = Item.objects.filter(id=random_id).first()
    if item:
        return item
    return Item.objects.order_by('?').first() if Item.objects.exists() else None