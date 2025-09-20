# management/commands/sync_market.py
from django.core.management.base import BaseCommand
from shop.tasks import sync_category_products_task


class Command(BaseCommand):
    help = "Синхронизировать все активные категории с Яндекс.Маркетом"

    def handle(self, *args, **options):
        from shop.models import Category
        categories = Category.objects.filter(is_active=True)
        for cat in categories:
            sync_category_products_task.delay(cat.title)
            self.stdout.write(f"Запущено: {cat.title}")